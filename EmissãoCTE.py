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

print("Iniciando Robô de Emissão de CTE...")

# =====================================================================
# CONFIGURAÇÃO DO NAVEGADOR
# =====================================================================
opcoes = Options()
opcoes.add_argument("--start-maximized")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)
espera = WebDriverWait(navegador, 15)

try:
    # =====================================================================
    # ETAPA 1: EXTRAIR DADOS DO PORTAL DE ORIGEM
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
    print("Login no Portal realizado com sucesso!")

    # =====================================================================
    # ETAPA 1.5: ABRIR E FIXAR BARRA LATERAL
    # =====================================================================
    print("Verificando a barra lateral...")
    try:
        gatilho_lateral = espera.until(
            EC.presence_of_element_located((By.XPATH, "//div[@title='Passar o mouse para abrir o menu']")))
        ActionChains(navegador).move_to_element(gatilho_lateral).perform()
        time.sleep(1)

        botao_alfinete = espera.until(EC.presence_of_element_located((
            By.XPATH,
            "//button[contains(@title, 'barra lateral') or .//*[name()='svg'][contains(@class, 'lucide-pin')]]"
        )))

        titulo_botao = botao_alfinete.get_attribute("title") or ""

        if "desfixar" not in titulo_botao.lower():
            navegador.execute_script("arguments[0].click();", botao_alfinete)
            print("✅ Alfinete clicado com sucesso!")
        else:
            print("ℹ️ A barra lateral já está fixada.")
        time.sleep(2)

    except Exception as e:
        print(f"Aviso: Não foi possível interagir com o alfinete. Erro: {e}")

    # =====================================================================
    # ETAPA 1.6: SELECIONAR SOLICITANTE (AMAZON)
    # =====================================================================
    print("Abrindo menu do usuário...")
    try:
        botao_usuario = espera.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='Selecionar solicitante']")))
        navegador.execute_script("arguments[0].click();", botao_usuario)
        time.sleep(1)

        opcao_amazon = espera.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Amazon')]")))
        navegador.execute_script("arguments[0].click();", opcao_amazon)
        print("✅ Solicitante Amazon selecionado!")
        time.sleep(2)

    except Exception as e:
        print(f"Aviso: Falha ao selecionar a Amazon. Erro: {e}")

    # =====================================================================
    # ETAPA 1.7: ACESSAR A PÁGINA DE EMISSÃO E FILTRAR
    # =====================================================================
    print("Navegando para Emissão e filtrando Pendentes...")
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
        time.sleep(2.5)

    except Exception as e:
        print(f"Aviso: Problema nos filtros. Erro: {e}")

    # =====================================================================
    # ETAPA 1.9: ACESSAR NOTA DISPONÍVEL
    # =====================================================================
    print("Buscando nota livre...")
    botoes_emitir = espera.until(EC.presence_of_all_elements_located((By.XPATH, "//button[contains(., 'Emitir')]")))
    nota_acessada = False

    for index, botao in enumerate(botoes_emitir):
        print(f"Tentando acessar nota {index + 1}...")
        navegador.execute_script("arguments[0].click();", botao)
        time.sleep(2)

        avisos_bloqueio = navegador.find_elements(By.XPATH, "//*[contains(text(), 'Rota já atribuída')]")

        if len(avisos_bloqueio) > 0:
            botao_entendi = navegador.find_element(By.XPATH, "//button[contains(., 'Entendi')]")
            navegador.execute_script("arguments[0].click();", botao_entendi)
            time.sleep(1)
            continue

        telas_emissao = navegador.find_elements(By.XPATH, "//*[contains(text(), 'Anexar Documentos de Emissão')]")

        if len(telas_emissao) > 0:
            print("✅ Nota livre acessada!")
            nota_acessada = True

            # -----------------------------------------------------
            # EXTRAINDO VRID
            # -----------------------------------------------------
            time.sleep(1)
            elemento_vrid = espera.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'ID: ')]")))
            vrid_limpo = elemento_vrid.text.replace("ID:", "").strip()
            print(f"🎯 VRID extraído: {vrid_limpo}")

            # -----------------------------------------------------
            # ABRINDO SSW
            # -----------------------------------------------------
            print("Abrindo SSW em nova aba...")
            navegador.execute_script("window.open('');")
            navegador.switch_to.window(navegador.window_handles[1])
            navegador.get("https://sistema.ssw.inf.br/")
            time.sleep(3)

            print("Logando no SSW...")
            navegador.find_element(By.ID, '1').send_keys(credenciais.SSW_DOMINIO)
            navegador.find_element(By.ID, '2').send_keys(credenciais.SSW_CPF)
            navegador.find_element(By.ID, '3').send_keys(credenciais.SSW_USUARIO)
            navegador.find_element(By.ID, '4').send_keys(credenciais.SSW_SENHA)
            navegador.find_element(By.ID, "5").click()
            time.sleep(5)
            print("✅ Login SSW!")

            # =====================================================================
            # ETAPA 3: TELA 071
            # =====================================================================
            print("Indo para a tela 71...")
            campo_unidade = espera.until(EC.element_to_be_clickable((By.ID, "2")))
            campo_unidade.click()
            campo_unidade.send_keys(Keys.CONTROL, "a")
            campo_unidade.send_keys(Keys.BACKSPACE)
            campo_unidade.send_keys("MGE")
            time.sleep(0.5)

            campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
            campo_opcao.click()
            campo_opcao.send_keys(Keys.CONTROL, "a")
            campo_opcao.send_keys(Keys.BACKSPACE)
            campo_opcao.send_keys("71")
            time.sleep(0.5)
            campo_opcao.send_keys(Keys.ENTER)

            time.sleep(5)  # Espera simples e eficaz

            # Pula para a última aba que abriu
            navegador.switch_to.window(navegador.window_handles[-1])
            navegador.maximize_window()

            # =====================================================================
            # ETAPA 4: PREENCHER A TELA 071 E PESQUISAR
            # =====================================================================
            print("Calculando data de 3 dias atrás...")
            # Pega a data atual, diminui 3 dias e formata como DDMMAA (ex: 140926)
            data_retroativa = (datetime.now() - timedelta(days=1)).strftime("%d%m%y")

            print(f"Alterando o Período de Importação para: {data_retroativa}")
            campo_data_ini = espera.until(EC.presence_of_element_located((By.ID, "fld_data_ini")))
            campo_data_ini.click()
            campo_data_ini.send_keys(Keys.CONTROL, "a")
            campo_data_ini.send_keys(Keys.BACKSPACE)
            campo_data_ini.send_keys(data_retroativa)
            time.sleep(2)

            print(f"Preenchendo o campo Romaneio/Packing List com o VRID: {vrid_limpo}")
            campo_packing_list = espera.until(EC.presence_of_element_located((By.ID, "fld_packing_list")))
            campo_packing_list.click()
            campo_packing_list.send_keys(Keys.CONTROL, "a")
            campo_packing_list.send_keys(Keys.BACKSPACE)
            campo_packing_list.send_keys(vrid_limpo)
            time.sleep(1)
            campo_packing_list.send_keys(Keys.ENTER)

            time.sleep(30)  # Espera a tabela carregar e abrir a nova janela

            # Pula para a janela da lista que acabou de abrir
            navegador.switch_to.window(navegador.window_handles[-1])
            navegador.maximize_window()

            # =====================================================================
            # ETAPA 5: CLICANDO NA NOTA E COPIANDO CNPJ
            # =====================================================================
            print("Abrindo detalhes da primeira nota...")

            # Pega o 1º link dentro da tabela de resultados, ignorando IDs dinâmicos
            primeira_nota = espera.until(EC.presence_of_element_located((By.XPATH, "(//table[@id='tblsr']//a)[1]")))

            # Força o clique pelo JavaScript para não ter erro de tela bloqueada
            navegador.execute_script("arguments[0].click();", primeira_nota)
            print("✅ Clique na primeira nota realizado com sucesso!")

            time.sleep(10)  # Espera a janela dos dados carregar

            print("Pulando para a janela com os detalhes...")
            navegador.switch_to.window(navegador.window_handles[-1])
            navegador.maximize_window()

            print("Extraindo CNPJ do Pagador...")
            time.sleep(2)

            try:
                # Busca a div 'data' que fica logo após o texto 'Pagador:'
                elemento_pagador = espera.until(EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(text(), 'Pagador:')]/following-sibling::div[@class='data']"
                )))

                texto_pagador = elemento_pagador.text
                # Corta no "-" e pega só os números, removendo espaços
                cnpj_pagador = texto_pagador.split("-")[0].strip()
                print(f"🎯 CNPJ do Pagador extraído: {cnpj_pagador}")

            except Exception as e:
                print("Aviso: Não consegui extrair o CNPJ.")
                cnpj_pagador = ""

                
            # =====================================================================
            # ETAPA 6: LIMPANDO O LIXO DE ABAS DO SSW E INDO PARA A TELA 6
            # =====================================================================
            print("Limpando janelas de consulta e voltando ao Menu...")

            # Enquanto tiver mais de 2 janelas abertas (Portal[0] e Menu[1]), fecha a última
            while len(navegador.window_handles) > 2:
                navegador.switch_to.window(navegador.window_handles[-1])
                navegador.close()
                time.sleep(0.5)

            # Agora só temos o portal e o Menu principal. Foca no Menu!
            navegador.switch_to.window(navegador.window_handles[1])

            print("Digitando a opção 6...")
            campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
            campo_opcao.click()
            campo_opcao.send_keys(Keys.CONTROL, "a")
            campo_opcao.send_keys(Keys.BACKSPACE)
            campo_opcao.send_keys("6")
            time.sleep(0.5)
            campo_opcao.send_keys(Keys.ENTER)

            time.sleep(5)

            navegador.switch_to.window(navegador.window_handles[-1])
            navegador.maximize_window()

            print(f"✅ Tela 6 pronta! | MEMÓRIA -> VRID: {vrid_limpo} | CNPJ: {cnpj_pagador}")

            break  # Encerra o For das notas

    if not nota_acessada:
        print("Aviso: Todas as notas desta página já estão ocupadas.")

except Exception as e:
    print(f"Erro crítico no fluxo: {e}")

print("✅ Fim do ciclo de automação.")