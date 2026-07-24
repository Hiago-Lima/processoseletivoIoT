from machine import Pin
# ligações
led_vermelho = Pin(21, Pin.OUT)   # Crítico
led_verde = Pin(22, Pin.OUT)      # Cheio
led_amarelo = Pin(23, Pin.OUT)    # Regular
clk = Pin(17, Pin.OUT)
dt = Pin(16, Pin.IN)
# constantes
PESO_CHEIO = 5000          # carga máxima nominal da caixa
LEITURA_BRUTA_MAXIMA = 2100 # leitura bruta máxima do sensor, isso é o valor que o sensor HX711 retorna quando a carga máxima nominal é aplicada, ele foi encontrado no site do wokwi 
LIMITE_SEGURANCA = 300     # abaixo disso o estoque deixa de ser "regular"
TOLERANCIA_CHEIO = 100     # margem para considerar "voltou a ficar cheio"
# classe do sensor de peso e suas funções
class HX711:
    # Implementação da leitura do sensor HX711
    # Retorna o valor lido do sensor
    def __init__(self, dt_pin, clk_pin, fator_escala):
        self.dt = dt_pin
        self.clk = clk_pin
        self.clk.value(0)  # Inicializa o pino de clock em LOW
        self.fator_escala = fator_escala

    def leitura_bruta(self):
        while self.dt.value() == 1: # Espera até que o pino DT fique em LOW, porque o sensor HX711 envia os dados quando DT está em LOW
            pass  
        valor = 0
        for i in range(24): # Lê 24 bits do sensor(é a maneira que o sensor HX711 envia os dados)
            self.clk.value(1)  # Seta o pino de clock em HIGH
            valor = (valor << 1) | self.dt.value()  # Lê o bit do pino DT e adiciona e desloca para a esquerda para formar o valor de 24 bits
            self.clk.value(0)  # Seta o pino de clock em LOW, fecha o pulso de clock
        # depois disso há o 25  pulso de clock que é usado para definir o ganho do sensor, mas não precisamos dele para a leitura do peso, então apenas damos o pulso e não usamos o valor
        self.clk.value(1) 
        self.clk.value(0) 
        if valor & 0x800000:    # verifica se o bit mais significativo é 1, o que indica que o valor é negativo em complemento de dois
            valor -= 0x1000000  # subtrai 2^24 para converter o valor para um inteiro negativo
        # isso é necessário porque o sensor HX711 envia os dados em complemento de dois, então precisamos converter para um valor inteiro normal( isso está explicado no datasheet do sensor HX711)
        return valor

    # retorna o peso em gramas, multiplicando a leitura bruta pelo fator de escala

    def leitura_peso(self):
        bruto = self.leitura_bruta()
        peso = bruto * self.fator_escala # o valor bruto lido do sensor é multiplicado pelo fator de escala para obter o peso em gramas
        if peso < 0: # se o peso for negativo, significa que o sensor está fora de calibração ou houve algum erro na leitura, então retornamos 0 para evitar valores negativos
            peso = 0
        return peso

sensor = HX711(dt, clk, PESO_CHEIO / LEITURA_BRUTA_MAXIMA)  # cria uma instância do sensor HX711 com os pinos DT e CLK e o fator de escala calculado
# o fator de escala é calculado dividindo a carga máxima nominal da caixa pelo valor bruto máximo do sensor, isso nos dá a relação entre o valor bruto lido e o peso real em gramas, basicamente uma regra de 3 simples, se o sensor HX711 retorna 2100 quando a carga máxima nominal é aplicada, então cada unidade bruta do sensor equivale a PESO_CHEIO / LEITURA_BRUTA_MAXIMA gramas

# saida dos leds
def atualizar_leds(estado):
    led_amarelo.value(1 if estado == "REGULAR" else 0)
    led_verde.value(1 if estado == "CHEIO" else 0)
    led_vermelho.value(1 if estado == "CRITICO" else 0)
    # anomalia nao acende nenhum led, apenas envia alerta, pois nao é um estado de estoque, mas sim um estado de erro do sensor

# FSM
alerta_vazio_enviado = False
reposicao_pendente = False
alerta_anomalia_enviado = False
# com essas variáveis de estado, podemos controlar o fluxo do sistema e evitar que os alertas sejam enviados repetidamente, garantindo que o sistema funcione de forma eficiente
# logicas

def avaliar_estoque(peso):
    global alerta_vazio_enviado, reposicao_pendente, alerta_anomalia_enviado # necessario pq o python entende que essas variáveis são locais a função, então precisamos declarar que elas são globais para poder modificar o valor delas dentro da função

    # Caso 1, anomalia do sensor 
    if peso == 0:
        if not alerta_anomalia_enviado:
            print("ALERTA: Caixa ausente ou erro de calibração no sensor HX711!")
            alerta_anomalia_enviado = True
        atualizar_leds("ANOMALIA")
        return
 
    alerta_anomalia_enviado = False
 
    # Caso 2, estoque crítico, caixa vazia
    if peso <= LIMITE_SEGURANCA:
        if not alerta_vazio_enviado:
            print("Evento de reposição disparado! Caixa vazia detectada.")
            alerta_vazio_enviado = True
            reposicao_pendente = True
        atualizar_leds("CRITICO")
        return
 
    # Caso 3, reabastecimento concluído, caixa cheia
    if reposicao_pendente and peso >= (PESO_CHEIO - TOLERANCIA_CHEIO):
        print("Abastecimento concluído. Caixa cheia.")
        reposicao_pendente = False
        alerta_vazio_enviado = False
        atualizar_leds("CHEIO")
        return
 
    # Caso 4, estoque regular, caixa parcialmente cheia
    if not reposicao_pendente:
        print(f"Status: Estoque Regular ({int(peso)}g)") 
        atualizar_leds("REGULAR")
 

print("Sistema Kanban Inicializado")
while True: # loop principal do sistema, que fica lendo o peso da caixa e avaliando o estoque continuamente
    peso_atual = sensor.ler_peso()
    avaliar_estoque(peso_atual) 

