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

# =====================================================================
# ETAPA 1: LOGIN NO PORTAL
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
# ETAPA 1.5: FIXAR BARRA LATERAL
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
# ETAPA 1.7: NAVEGAR PARA EMISSÃO E FILTRAR PENDENTES
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
# LOOP PRINCIPAL - PROCESSA TODAS AS NOTAS ATÉ ACABAR
# =====================================================================
numero_nota = 0

while True:
    numero_nota += 1
    print(f"\n{'='*60}")
    print(f"PROCESSANDO NOTA #{numero_nota}")
    print(f"{'='*60}")

    # Garante foco no portal e atualiza a lista
    navegador.switch_to.window(navegador.window_handles[0])
    navegador.refresh()
    time.sleep(3)

    # Reaplicar filtro Pendentes após refresh
    try:
        filtro_status = espera.until(EC.element_to_be_clickable(
            (By.XPATH, "//label[contains(text(), 'Status Emissão')]/following-sibling::button[@role='combobox']")))
        navegador.execute_script("arguments[0].click();", filtro_status)
        time.sleep(1)

        opcao_pendentes = espera.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@role='option' and contains(., 'Pendentes')] | //div[text()='Pendentes']")))
        navegador.execute_script("arguments[0].click();", opcao_pendentes)
        time.sleep(2.5)
    except Exception as e:
        print(f"Aviso nos filtros: {e}")

    # Busca notas MG disponíveis
    xpath_mg = "//tr[.//div[contains(text(), ' - MG') or contains(@title, ' - MG')]]//button[contains(., 'Emitir')]"
    try:
        botoes_emitir = espera.until(EC.presence_of_all_elements_located((By.XPATH, xpath_mg)))
        print(f"Encontrada(s) {len(botoes_emitir)} nota(s) de MG nesta página.")
    except Exception:
        print("Nenhuma nota MG encontrada. Encerrando robô.")
        break

    nota_acessada = False
    placa_dinamica = ""
    vrid_limpo = ""
    cnpj_pagador = "FALHOU"

    # ------------------------------------------------------------------
    # TENTA ACESSAR A PRÓXIMA NOTA LIVRE
    # ------------------------------------------------------------------
    for index, botao in enumerate(botoes_emitir):
        linha = botao.find_element(By.XPATH, "./ancestor::tr")
        try:
            span_nome = linha.find_element(By.XPATH, ".//td[1]//span[contains(@class, 'truncate')]")
            nome_emitente = span_nome.text.strip()
            if nome_emitente != "":
                print(f"⏭️ Pulando nota MG {index + 1}: ocupada por '{nome_emitente}'.")
                continue
        except:
            pass

        print(f"Tentando acessar a nota MG {index + 1} (Livre)...")
        navegador.execute_script("arguments[0].click();", botao)
        time.sleep(2)

        if navegador.find_elements(By.XPATH, "//*[contains(text(), 'Rota já atribuída')]"):
            navegador.find_element(By.XPATH, "//button[contains(., 'Entendi')]").click()
            time.sleep(1)
            continue

        if navegador.find_elements(By.XPATH, "//*[contains(text(), 'Anexar Documentos de Emissão')]"):
            print("✅ Nota livre de MG acessada!")
            nota_acessada = True

            # Extrai VRID
            elemento_vrid = espera.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'ID: ')]")))
            vrid_limpo = elemento_vrid.text.replace("ID:", "").strip()
            print(f"🎯 VRID extraído: {vrid_limpo}")

            # Extrai Placa
            try:
                elemento_placa = espera.until(EC.presence_of_element_located((
                    By.XPATH,
                    "//*[contains(text(), 'PLACAS')]/following-sibling::*[1] | //*[contains(text(), 'PLACAS')]/.."
                )))
                texto_placa = elemento_placa.text.replace("PLACAS", "").strip()
                placa_dinamica = texto_placa.split('\n')[0].strip()
                print(f"🎯 Placa extraída: {placa_dinamica}")
            except:
                print("Aviso: Não consegui extrair a placa do portal.")
                placa_dinamica = ""

            break

    if not nota_acessada:
        print("Nenhuma nota livre encontrada. Encerrando robô.")
        break

    # ------------------------------------------------------------------
    # ETAPA 3: ABRIR SSW E FAZER LOGIN
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # ETAPA 4: TELA 071
    # ------------------------------------------------------------------
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
    time.sleep(5)

    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()

    # ------------------------------------------------------------------
    # ETAPA 5: PREENCHER TELA 071 E PESQUISAR NF
    # ------------------------------------------------------------------
    data_retroativa = (datetime.now() - timedelta(days=1)).strftime("%d%m%y")
    print(f"Alterando o Período de Importação para: {data_retroativa}")

    campo_data_ini = espera.until(EC.presence_of_element_located((By.ID, "fld_data_ini")))
    campo_data_ini.click()
    campo_data_ini.send_keys(Keys.CONTROL, "a")
    campo_data_ini.send_keys(Keys.BACKSPACE)
    campo_data_ini.send_keys(data_retroativa)
    time.sleep(2)

    print(f"Preenchendo Romaneio/Packing List com VRID: {vrid_limpo}")
    campo_packing_list = espera.until(EC.presence_of_element_located((By.ID, "fld_packing_list")))
    campo_packing_list.click()
    campo_packing_list.send_keys(Keys.CONTROL, "a")
    campo_packing_list.send_keys(Keys.BACKSPACE)
    campo_packing_list.send_keys(vrid_limpo)
    time.sleep(1)
    campo_packing_list.send_keys(Keys.ENTER)
    time.sleep(30)

    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()

    # ------------------------------------------------------------------
    # ETAPA 6: EXTRAIR CNPJ DA NOTA
    # ------------------------------------------------------------------
    print("Aguardando a janela com a lista de notas abrir...")
    espera.until(EC.number_of_windows_to_be(4))

    print("Procurando a aba correta da Lista...")
    for aba in navegador.window_handles:
        navegador.switch_to.window(aba)
        if "> Lista" in navegador.title:
            print("✅ Foco na Janela da Lista!")
            break

    navegador.maximize_window()
    time.sleep(5)

    janelas_antes = navegador.window_handles

    print("Clicando na primeira nota...")
    primeira_nota = espera.until(EC.presence_of_element_located((
        By.XPATH, "//tr[@rid='0']//a[contains(@class, 'sra2')]"
    )))
    navegador.execute_script("arguments[0].click();", primeira_nota)
    print("✅ Primeira nota clicada!")

    espera.until(EC.number_of_windows_to_be(5))
    janelas_depois = navegador.window_handles
    aba_nova = [j for j in janelas_depois if j not in janelas_antes][0]

    navegador.switch_to.window(aba_nova)
    navegador.maximize_window()
    time.sleep(3)

    print("Extraindo CNPJ do Pagador...")
    try:
        elemento_pagador = espera.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[contains(text(), 'Pagador:')]/following-sibling::div[@class='data']"
        )))
        texto_pagador = elemento_pagador.text
        cnpj_pagador = texto_pagador.split("-")[0].strip()
        print(f"🎯 CNPJ extraído: {cnpj_pagador}")
    except Exception as e:
        print("Aviso: Não consegui extrair o CNPJ da nota.")

    # ------------------------------------------------------------------
    # ETAPA 7: FECHAR ABAS EXTRAS E IR PARA TELA 6
    # ------------------------------------------------------------------
    print("Limpando janelas e voltando ao Menu...")
    while len(navegador.window_handles) > 2:
        navegador.switch_to.window(navegador.window_handles[-1])
        navegador.close()
        time.sleep(3)

    navegador.switch_to.window(navegador.window_handles[1])

    print("Digitando a opção 6...")
    campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
    campo_opcao.click()
    campo_opcao.send_keys(Keys.CONTROL, "a")
    campo_opcao.send_keys(Keys.BACKSPACE)
    campo_opcao.send_keys("6")
    time.sleep(1)
    campo_opcao.send_keys(Keys.ENTER)
    time.sleep(5)

    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()
    print(f"✅ Tela 6 pronta! | VRID: {vrid_limpo} | CNPJ: {cnpj_pagador}")

    # ------------------------------------------------------------------
    # ETAPA 8: SELECIONAR E - EDI e G - REDESPACHO
    # ------------------------------------------------------------------
    print("Selecionando a opção 'E - EDI'...")
    janelas_antes_e = navegador.window_handles
    botao_e = espera.until(EC.presence_of_element_located((By.ID, "link_doc_e")))
    navegador.execute_script("arguments[0].click();", botao_e)
    print("✅ Opção 'E' clicada!")
    time.sleep(3)

    janelas_depois_e = navegador.window_handles
    if len(janelas_depois_e) > len(janelas_antes_e):
        aba_nova_e = [j for j in janelas_depois_e if j not in janelas_antes_e][0]
        navegador.switch_to.window(aba_nova_e)
        navegador.maximize_window()
        print("✅ Foco na janela 'E'.")

    print("Selecionando a opção 'G - Redespacho intermediário'...")
    janelas_antes_g = navegador.window_handles
    botao_g = espera.until(EC.presence_of_element_located((By.ID, "link_doc_g")))
    navegador.execute_script("arguments[0].click();", botao_g)
    print("✅ Opção 'G' clicada!")
    time.sleep(3)

    janelas_depois_g = navegador.window_handles
    if len(janelas_depois_g) > len(janelas_antes_g):
        aba_nova_g = [j for j in janelas_depois_g if j not in janelas_antes_g][0]
        navegador.switch_to.window(aba_nova_g)
        navegador.maximize_window()
        print("✅ Foco no formulário 'G'.")

    # ------------------------------------------------------------------
    # ETAPA 9: PREENCHER FORMULÁRIO
    # ------------------------------------------------------------------
    print("Inserindo CNPJ do Pagador...")
    if cnpj_pagador and cnpj_pagador != "FALHOU":
        campo_cnpj = espera.until(EC.presence_of_element_located((By.ID, "cgc_pagador")))
        campo_cnpj.click()
        campo_cnpj.send_keys(Keys.CONTROL, "a")
        campo_cnpj.send_keys(Keys.BACKSPACE)
        campo_cnpj.send_keys(cnpj_pagador)
        print(f"✅ CNPJ {cnpj_pagador} inserido!")
    else:
        print("⚠️ CNPJ vazio ou falhou.")

    data_primeiro_dia = datetime.now().replace(day=1).strftime("%d%m%y")
    campo_data_ini_tela6 = espera.until(EC.presence_of_element_located((By.ID, "data_ini")))
    campo_data_ini_tela6.click()
    campo_data_ini_tela6.send_keys(Keys.CONTROL, "a")
    campo_data_ini_tela6.send_keys(Keys.BACKSPACE)
    campo_data_ini_tela6.send_keys(data_primeiro_dia)
    time.sleep(3)

    print(f"Inserindo VRID ({vrid_limpo}) no Romaneio/Packing List...")
    campo_packing = espera.until(EC.presence_of_element_located((By.ID, "fld_packing")))
    campo_packing.click()
    campo_packing.send_keys(Keys.CONTROL, "a")
    campo_packing.send_keys(Keys.BACKSPACE)
    campo_packing.send_keys(vrid_limpo)
    time.sleep(3)

    placa_veiculo = placa_dinamica if placa_dinamica != "" else "RYE3H81"

    print(f"Inserindo placa ({placa_veiculo})...")
    campo_placa_coleta = espera.until(EC.presence_of_element_located((By.ID, "placa_coleta")))
    campo_placa_coleta.click()
    campo_placa_coleta.send_keys(Keys.CONTROL, "a")
    campo_placa_coleta.send_keys(Keys.BACKSPACE)
    campo_placa_coleta.send_keys(placa_veiculo)
    time.sleep(3)

    print("Inserindo Tipo de mercadoria (1)...")
    campo_merc = espera.until(EC.presence_of_element_located((By.ID, "cod_merc")))
    campo_merc.click()
    campo_merc.send_keys(Keys.CONTROL, "a")
    campo_merc.send_keys(Keys.BACKSPACE)
    campo_merc.send_keys("1")
    time.sleep(3)

    print("Inserindo Tabela Genérica S...")
    campo_tab = espera.until(EC.presence_of_element_located((By.ID, "tab_gen")))
    campo_tab.click()
    campo_tab.send_keys(Keys.CONTROL, "a")
    campo_tab.send_keys(Keys.BACKSPACE)
    campo_tab.send_keys("S")
    time.sleep(3)

    print(f"Inserindo placa provisória ({placa_veiculo})...")
    campo_placa_prov = espera.until(EC.presence_of_element_located((By.ID, "placa_prov")))
    campo_placa_prov.click()
    campo_placa_prov.send_keys(Keys.CONTROL, "a")
    campo_placa_prov.send_keys(Keys.BACKSPACE)
    campo_placa_prov.send_keys(placa_veiculo)
    time.sleep(3)

    # ------------------------------------------------------------------
    # ETAPA 10: CLICAR EM APONTAR NFs (1ª VEZ)
    # ------------------------------------------------------------------
    print("Clicando em 'Apontar NFs'...")
    janelas_antes_apontar = navegador.window_handles
    botao_apontar = espera.until(EC.presence_of_element_located((By.ID, "lnk_apontar")))
    navegador.execute_script("arguments[0].click();", botao_apontar)
    print("✅ 'Apontar NFs' clicado!")

    espera.until(EC.number_of_windows_to_be(len(janelas_antes_apontar) + 1))
    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()
    print("✅ Janela de Apontar NFs aberta!")
    time.sleep(30)

    # ------------------------------------------------------------------
    # ETAPA 11: 3 RODADAS DE SELEÇÃO E ENVIO
    # ------------------------------------------------------------------
    for rodada in range(1, 4):
        print(f"\n--- RODADA {rodada}/3 ---")

        if rodada > 1:
            # Volta para janela do formulário e clica em Apontar NFs novamente
            print("Clicando em Apontar NFs novamente...")
            navegador.switch_to.window(navegador.window_handles[-1])

            janelas_antes_apontar2 = navegador.window_handles
            botao_apontar2 = espera.until(EC.element_to_be_clickable((By.ID, "lnk_apontar")))
            navegador.execute_script("arguments[0].click();", botao_apontar2)

            espera.until(EC.number_of_windows_to_be(len(janelas_antes_apontar2) + 1))
            navegador.switch_to.window(navegador.window_handles[-1])
            navegador.maximize_window()
            print("✅ Nova janela de Apontar NFs aberta!")
            time.sleep(30)

        if rodada in [1, 2]:
            # Selecionar todas com checkbox
            print("Selecionando todas as notas (checkbox)...")
            checkbox_todas = WebDriverWait(navegador, 15).until(
                EC.element_to_be_clickable((By.ID, "c0")))
            navegador.execute_script("arguments[0].click();", checkbox_todas)
            print("✅ Todas as notas selecionadas!")
            time.sleep(2)

        else:
            # Rodada 3: Marcar todas as páginas
            print("Clicando em Marcar todas as páginas...")
            btn_marcar = WebDriverWait(navegador, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@class='baselnk' and contains(text(), 'Marcar')]")))
            navegador.execute_script("arguments[0].click();", btn_marcar)
            print("✅ Todas as páginas marcadas!")
            time.sleep(3)

        # Scroll até o final
        print("Dando scroll até o final da página...")
        navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Clicar na setinha (>)
        print("Clicando na setinha de avançar...")
        try:
            botao_avancar = WebDriverWait(navegador, 5).until(
                EC.element_to_be_clickable((By.XPATH, '(//a[@class="srimglnk" and @accesskey="&"])[1]')))
            navegador.execute_script("arguments[0].click();", botao_avancar)
            print("✅ Setinha clicada!")
        except Exception:
            print("ℹ Setinha não encontrada.")
        time.sleep(3)

        # Popup: Continuar
        print("Clicando em Continuar no popup...")
        try:
            btn_continuar = WebDriverWait(navegador, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@class='dialog' and contains(text(), 'Continuar')]")))
            navegador.execute_script("arguments[0].click();", btn_continuar)
            print("✅ Continuar clicado!")
        except Exception:
            print("ℹ Popup Continuar não encontrado.")
        time.sleep(8)

        # # Popup: 7.OK (aguarda até 5 minutos)
        # print("Aguardando popup 7.OK...")
        # try:
        #     botao_ok = WebDriverWait(navegador, 300).until(
        #         EC.element_to_be_clickable((By.XPATH, "//a[@class='dialog' and contains(text(), '7')]")))
        #     navegador.execute_script("arguments[0].click();", botao_ok)
        #     print("✅ 7.OK clicado!")
        # except Exception:
        #     print("⚠ Popup 7.OK não apareceu.")
        # time.sleep(5)
        #
        # # Volta para janela do formulário para próxima rodada
        # navegador.switch_to.window(navegador.window_handles[-1])
        # time.sleep(3)
        # Popup: 7.OK (aguarda até 5 minutos)
        print("Aguardando popup 7.OK...")
        try:
            # Procura em TODAS as janelas abertas
            janela_ok_encontrada = False
            for handle in navegador.window_handles:
                navegador.switch_to.window(handle)
                try:
                    botao_ok = WebDriverWait(navegador, 5).until(
                        EC.element_to_be_clickable((By.ID, "0")))
                    navegador.execute_script("arguments[0].click();", botao_ok)
                    print("✅ 7.OK clicado!")
                    janela_ok_encontrada = True
                    break
                except:
                    continue

            if not janela_ok_encontrada:
                print("⚠ Popup 7.OK não encontrado em nenhuma janela.")

        except Exception as e:
            print(f"⚠ Erro ao clicar em 7.OK: {e}")
        time.sleep(5)

    print(f"\n✅ Nota #{numero_nota} ({vrid_limpo}) concluída com sucesso!")

    # ------------------------------------------------------------------
    # FECHAR TODAS AS JANELAS EXTRAS E VOLTAR AO PORTAL
    # ------------------------------------------------------------------
    print("Fechando janelas extras e voltando ao portal...")
    while len(navegador.window_handles) > 1:
        navegador.switch_to.window(navegador.window_handles[-1])
        navegador.close()
        time.sleep(1)

    navegador.switch_to.window(navegador.window_handles[0])
    time.sleep(3)
    print("✅ De volta ao portal! Buscando próxima nota...")

# =====================================================================
# FIM DO LOOP
# =====================================================================
print("\n✅ Robô finalizado! Todas as notas foram processadas.")
time.sleep(30)