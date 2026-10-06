# EMISSÃO DE MANIFESTO

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
import re

# =====================================================================
# CONFIGURAÇÃO DO NAVEGADOR
# =====================================================================
opcoes = Options()
opcoes.add_argument("--start-maximized")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)
espera = WebDriverWait(navegador, 15)

# =====================================================================
# ETAPA 1: LOGIN E NAVEGAÇÃO NO PORTAL
# =====================================================================
print("Acessando o Portal Emissor...")
navegador.get("https://portal-dedicado.vercel.app/login")

print("Realizando Login no Portal...")
campo_usuario = espera.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Usuário']")))
campo_usuario.send_keys(credenciais.PORTAL_USER)
time.sleep(0.5)

campo_senha = navegador.find_element(By.XPATH, "//input[@placeholder='Senha']")
campo_senha.send_keys(credenciais.PORTAL_SENHA)
time.sleep(0.5)

botao_entrar = navegador.find_element(By.XPATH, "//button[@type='submit']")
botao_entrar.click()
time.sleep(5)
print("✅ Login no Portal realizado!")

# Fixar Barra Lateral
try:
    gatilho_lateral = espera.until(
        EC.presence_of_element_located((By.XPATH, "//div[@title='Passar o mouse para abrir o menu']")))
    ActionChains(navegador).move_to_element(gatilho_lateral).perform()
    time.sleep(1)
    botao_alfinete = espera.until(EC.presence_of_element_located((
        By.XPATH, "//button[contains(@title, 'barra lateral') or .//*[name()='svg'][contains(@class, 'lucide-pin')]]"
    )))
    if "desfixar" not in (botao_alfinete.get_attribute("title") or "").lower():
        navegador.execute_script("arguments[0].click();", botao_alfinete)
    time.sleep(2)
except Exception:
    pass

# Selecionar Amazon
try:
    botao_usuario = espera.until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Selecionar solicitante']")))
    navegador.execute_script("arguments[0].click();", botao_usuario)
    time.sleep(1)
    opcao_amazon = espera.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Amazon')]")))
    navegador.execute_script("arguments[0].click();", opcao_amazon)
    time.sleep(2)
except Exception:
    pass

# Navegar para Pendentes
try:
    botao_emissao = espera.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/emissao']")))
    navegador.execute_script("arguments[0].click();", botao_emissao)
    time.sleep(3)
    filtro_status = espera.until(EC.element_to_be_clickable(
        (By.XPATH, "//label[contains(text(), 'Status Emissão')]/following-sibling::button[@role='combobox']")))
    navegador.execute_script("arguments[0].click();", filtro_status)
    time.sleep(1)
    opcao_pendentes = espera.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[@role='option' and contains(., 'Pendentes')] | //div[text()='Pendentes']")))
    navegador.execute_script("arguments[0].click();", opcao_pendentes)
    time.sleep(5)
except Exception:
    pass

# =====================================================================
# ETAPA 2: INTELIGÊNCIA DE EXTRAÇÃO (PORTAL)
# =====================================================================
print("Buscando notas (Com Nome OU Borda Vermelha) e do tipo Carreteiro (C)...")

linhas_tabela = espera.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody//tr")))

# INICIALIZAÇÃO CORRETA DE TODAS AS VARIÁVEIS
vrid_extraido = ""
placa_extraida = ""
cidade_origem = ""
estado_origem = ""
cidade_destino = ""
data_previsao = ""
hora_previsao = ""
valor_pagar = ""
pagamento_extraido = ""
pix_extraido = ""
nota_encontrada = False

for index, linha in enumerate(linhas_tabela):
    try:
        # 1. Verifica se tem BORDA VERMELHA
        alerta = linha.find_elements(By.XPATH,
                                     ".//td[1]//div[contains(@class, 'border-red-500') or contains(@class, 'animate-pulse')]")
        tem_borda_vermelha = len(alerta) > 0

        # 2. Verifica se tem NOME
        tem_nome = False
        nome_emitente = ""
        spans_nome = linha.find_elements(By.XPATH, ".//td[1]//span[contains(@class, 'truncate')]")
        if len(spans_nome) > 0:
            nome_emitente = spans_nome[0].text.strip()
            if nome_emitente != "":
                tem_nome = True

        # 3. REGRA DE DECISÃO: Pula a linha se NÃO tiver nome E NÃO tiver borda vermelha
        if not (tem_nome or tem_borda_vermelha):
            continue

        # 4. Verifica se o Tipo é 'C' (Carreteiro)
        span_tipo = linha.find_elements(By.XPATH, ".//span[@title='Relacionamento: CARRETEIRO' or text()='C']")

        if len(span_tipo) > 0:
            motivo = f"Nome ('{nome_emitente}') + Borda Vermelha" if (tem_nome and tem_borda_vermelha) else (
                f"Nome ('{nome_emitente}')" if tem_nome else "Borda Vermelha")
            print(f"✅ Linha {index + 1} validada! (Motivo: {motivo} | Tipo: C)")

            # --- EXTRAÇÃO DE DADOS BÁSICOS ---
            # Origem e Estado
            try:
                texto_origem = linha.find_element(By.XPATH, ".//td[4]").text
                linha_origem = texto_origem.split('\n')[0]  # Pega ex: "CAJAMAR - SP"

                if "-" in linha_origem:
                    cidade_origem = linha_origem.split('-')[0].strip()
                    estado_origem = linha_origem.split('-')[1].strip()
                elif "/" in linha_origem:
                    cidade_origem = linha_origem.split('/')[0].strip()
                    estado_origem = linha_origem.split('/')[1].strip()
                else:
                    cidade_origem = linha_origem.strip()
                    estado_origem = "MG"  # Padrão de segurança
            except Exception:
                cidade_origem = "CONTAGEM"
                estado_origem = "MG"

            # Previsão de Chegada e Cidade de Destino - FORMATO SSW (DDMMAA)
            try:
                texto_destino = linha.find_element(By.XPATH, ".//td[5]").text

                # Extrai o nome da Cidade de Destino
                cidade_destino = texto_destino.split('\n')[0].split(' - ')[0].strip()

                # Trata a DATA e HORA
                linha_data_hora = texto_destino.split('\n')[1]  # Ex: "24/09/2026 - 02:59"

                data_bruta = linha_data_hora.split(' - ')[0].strip()
                partes_data = data_bruta.split('/')
                data_previsao = f"{partes_data[0]}{partes_data[1]}{partes_data[2][-2:]}"

                hora_previsao = linha_data_hora.split(' - ')[1].strip().replace(":", "")
            except Exception:
                cidade_destino = ""
                data_previsao = ""
                hora_previsao = ""

            # VRID
            vrid_extraido = linha.find_element(By.XPATH, ".//td[2]").text.strip()

            # Placa (Inteligência Regex)
            texto_linha = linha.text.upper()
            padrao_placa = re.search(r'\b[A-Z]{3}-?[0-9][A-Z0-9][0-9]{2}\b', texto_linha)
            if padrao_placa:
                placa_extraida = padrao_placa.group(0).replace("-", "").strip()
            else:
                try:
                    placa_extraida = linha.find_element(By.XPATH, ".//td[contains(@class, 'font-mono')]").text.strip()
                except:
                    placa_extraida = ""

            # --- EXTRAÇÃO DE VALOR E DADOS DO POP-UP ---
            # Valor a Pagar (INTELIGÊNCIA ATUALIZADA: Pega o último valor R$ da linha)
            try:
                campos_valor = linha.find_elements(By.XPATH, ".//td[contains(text(), 'R$')]")

                if len(campos_valor) > 1:
                    texto_valor = campos_valor[-1].text
                elif len(campos_valor) == 1:
                    texto_valor = campos_valor[0].text
                else:
                    texto_valor = "0,00"

                valor_pagar = texto_valor.replace("R$", "").replace(".", "").strip()
            except Exception:
                valor_pagar = "0,00"

            # Abrir Pop-up (Emitir) para capturar PIX e % de Pagamento
            pagamento_extraido = "100%"
            pix_extraido = ""
            try:
                botao_emitir = linha.find_element(By.XPATH,
                                                  ".//button[contains(text(), 'Emitir') or contains(@class, 'bg-emerald')]")
                navegador.execute_script("arguments[0].click();", botao_emitir)
                print("Aguardando pop-up do portal para extrair PIX e Pagamento...")
                time.sleep(2)

                # Procura a % de Pagamento
                try:
                    pagamento_extraido = navegador.find_element(By.XPATH,
                                                                "//*[contains(text(), 'PAGAMENTO')]/following-sibling::*[1]").text.strip()
                except Exception:
                    pass

                # Procura o PIX (Estratégia Dupla)
                try:
                    # 1ª Tentativa
                    pix_extraido = navegador.find_element(By.XPATH,
                                                          "//*[text()='PIX' or contains(text(), 'PIX')]/following-sibling::*[1]").text.strip()
                except Exception:
                    pass

                if not pix_extraido:
                    try:
                        # 2ª Tentativa (Bloco inteiro)
                        bloco_pix = navegador.find_element(By.XPATH,
                                                           "//*[text()='PIX' or contains(text(), 'PIX')]/..").text
                        pix_extraido = \
                        bloco_pix.replace("PIX", "").replace("DADOS PROPRIETÁRIO", "").strip().split("\n")[0]
                    except Exception:
                        pass

                # Clica em Cancelar para fechar o pop-up da nota
                botao_cancelar = navegador.find_element(By.XPATH, "//button[contains(text(), 'Cancelar')]")
                navegador.execute_script("arguments[0].click();", botao_cancelar)
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Erro ao abrir pop-up para extrair PIX/Pagamento: {e}")

            print(
                f"🎯 Dados: VRID {vrid_extraido} | Placa {placa_extraida} | Origem {cidade_origem}-{estado_origem} | Destino {cidade_destino} | Data {data_previsao} | Valor {valor_pagar} | Pag {pagamento_extraido} | PIX {pix_extraido}")
            nota_encontrada = True
            break

    except Exception as e:
        pass

placa_extraida = ""
if not nota_encontrada:
    print("Nenhuma nota com Nome/Borda Vermelha do tipo 'C' foi encontrada. Encerrando.")
    navegador.quit()
    exit()

# =====================================================================
# ETAPA 3: LOGIN NO SSW (EM NOVA ABA)
# =====================================================================
print("Abrindo SSW em nova aba...")
navegador.execute_script("window.open('');")
navegador.switch_to.window(navegador.window_handles[-1])
navegador.get("https://sistema.ssw.inf.br/")
time.sleep(3)

print("Logando no SSW...")
navegador.find_element(By.ID, '1').send_keys(credenciais.SSW_DOMINIO)
navegador.find_element(By.ID, '2').send_keys(credenciais.SSW_CPF)
navegador.find_element(By.ID, '3').send_keys(credenciais.SSW_USUARIO)
navegador.find_element(By.ID, '4').send_keys(credenciais.SSW_SENHA)
navegador.find_element(By.ID, "5").click()
time.sleep(3)

# =====================================================================
# ETAPA 4: NAVEGAR PARA TELA 20 E PREENCHER DADOS DA PLACA
# =====================================================================
print(f"Definindo a unidade do SSW com base no estado ({estado_origem})...")

# Inteligência: Pega os 2 primeiros caracteres, transforma em maiúsculo e adiciona o "E"
unidade_ssw = f"{str(estado_origem)[:2].upper()}E"
print(f"✅ Unidade SSW definida automaticamente como: {unidade_ssw}")

print("Indo para a tela 72...")
campo_unidade = espera.until(EC.element_to_be_clickable((By.ID, "2")))
campo_unidade.click()
campo_unidade.send_keys(Keys.CONTROL, "a")
campo_unidade.send_keys(Keys.BACKSPACE)
campo_unidade.send_keys(unidade_ssw)
time.sleep(1)

janelas_antes_72 = navegador.window_handles

campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
campo_opcao.click()
campo_opcao.send_keys(Keys.CONTROL, "a")
campo_opcao.send_keys(Keys.BACKSPACE)
campo_opcao.send_keys("20")
time.sleep(1)
campo_opcao.send_keys(Keys.ENTER)

print("A aguardar que a janela 72 abra...")
espera.until(EC.number_of_windows_to_be(len(janelas_antes_72) + 1))

janelas_depois_72 = navegador.window_handles
aba_nova_72 = [j for j in janelas_depois_72 if j not in janelas_antes_72][0]

navegador.switch_to.window(aba_nova_72)
navegador.maximize_window()
print(f"✅ Foco alterado para a Tela 20 com sucesso (Unidade: {unidade_ssw})!")

time.sleep(5)

# ------------------------------------------------------------------
# PREENCHER PLACA NA TELA 20
# ------------------------------------------------------------------
print(f"A preencher a placa ({placa_extraida})...")

campo_placa = WebDriverWait(navegador, 10).until(
    EC.presence_of_element_located((By.ID, "placa_provisoria"))
) # Parêntese fechado corretamente aqui!

navegador.execute_script("arguments[0].scrollIntoView(true);", campo_placa)
time.sleep(0.5)

# 1. OPÇÃO NUCLEAR (JavaScript): Limpa o campo diretamente no HTML do SSW
navegador.execute_script("arguments[0].value = '';", campo_placa)
time.sleep(0.5)

# 2. Injeta a placa diretamente no valor do elemento (Ignora bloqueios de teclado)
navegador.execute_script("arguments[0].value = arguments[1];", campo_placa, "RXT2563")
time.sleep(0.5)

# 3. Dá um clique e um TAB apenas para acionar as validações internas do SSW (se existirem)
campo_placa.click()
campo_placa.send_keys(Keys.TAB)
time.sleep(1)

# Clica no botão Digitação de CTRC.
try:
    btn_enviar = navegador.find_element(By.ID, "7")
    navegador.execute_script("arguments[0].click();", btn_enviar)
    print("✅ Botão de enviar clicado com sucesso!")
except Exception:
    campo_placa.send_keys(Keys.ENTER)
    print("✅ Placa enviada usando a tecla ENTER!")

time.sleep(25)

# ------------------------------------------------------------------
# PREENCHER TELA COM NUMERO NDO CTE - PARA AMARRAR
# ------------------------------------------------------------------
# MUDAR O FOCO PRA NOVA TELA. PREENCHER COM O NUMERO DO CTRC