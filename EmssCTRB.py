import time
from datetime import datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import credenciais
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

opcoes = Options()
opcoes.add_argument("--start-maximized")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)
espera = WebDriverWait(navegador, 15)

navegador.get("https://sistema.ssw.inf.br/")

print("Logando no SSW...")
navegador.find_element(By.ID, '1').send_keys(credenciais.SSW_DOMINIO)
navegador.find_element(By.ID, '2').send_keys(credenciais.SSW_CPF)
navegador.find_element(By.ID, '3').send_keys(credenciais.SSW_USUARIO)
navegador.find_element(By.ID, '4').send_keys(credenciais.SSW_SENHA)
navegador.find_element(By.ID, "5").click()

time.sleep(3)

# ------------------------------------------------------------------
# ETAPA 1: TELA 72
# ------------------------------------------------------------------
print("Indo para a tela 72...")
campo_unidade = espera.until(EC.element_to_be_clickable((By.ID, "2")))
campo_unidade.click()
campo_unidade.send_keys(Keys.CONTROL, "a")
campo_unidade.send_keys(Keys.BACKSPACE)
campo_unidade.send_keys("MGE")
time.sleep(1)

janelas_antes_72 = navegador.window_handles

campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
campo_opcao.click()
campo_opcao.send_keys(Keys.CONTROL, "a")
campo_opcao.send_keys(Keys.BACKSPACE)
campo_opcao.send_keys("72")
time.sleep(1)
campo_opcao.send_keys(Keys.ENTER)

print("A aguardar que a janela 72 abra...")
espera.until(EC.number_of_windows_to_be(len(janelas_antes_72) + 1))

janelas_depois_72 = navegador.window_handles
aba_nova_72 = [j for j in janelas_depois_72 if j not in janelas_antes_72][0]

navegador.switch_to.window(aba_nova_72)
navegador.maximize_window()
print("✅ Foco alterado para a Tela 72 com sucesso!")


print("A preencher a placa/ID...")
campo_placa = espera.until(EC.element_to_be_clickable((By.ID, "placa_veic")))
campo_placa.click()
campo_placa.send_keys(Keys.CONTROL, "a")
campo_placa.send_keys(Keys.BACKSPACE)
campo_placa.send_keys("RVX3D67")
time.sleep(2)
campo_placa.send_keys(Keys.ENTER)

time.sleep(10)





