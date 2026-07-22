from machine import Pin

# ligações
led_vermelho = Pin(21, Pin.OUT)   # Crítico
led_verde = Pin(22, Pin.OUT)      # Cheio
led_amarelo = Pin(23, Pin.OUT)    # Regular
clk = Pin(17, Pin.OUT)
dt = Pin(16, Pin.IN)
# constantes
PESO_CHEIO = 5000          # g - carga máxima nominal da caixa
LIMITE_SEGURANCA = 300     # g - abaixo disso o estoque deixa de ser "regular"
TOLERANCIA_CHEIO = 100     # g - margem para considerar "voltou a ficar cheio"
INTERVALO_LEITURA_MS = 200 # loop curto e não-bloqueante, tlvz mude isso dps

# leitura inicial do sensor
# saida dos leds
# logicas
print("Sistema Kanban Inicializado")

