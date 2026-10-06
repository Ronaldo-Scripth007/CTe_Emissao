# NESTA VERSÃO ESTOU EMITINDO APENAS UM CTE. MARCANDO TODAS AS NOTAS (FLAG)

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
# =====================================================================
# CONFIGURAÇÃO DO NAVEGADOR
# =====================================================================
# region CONFIGURAÇÃO DO NAVEGADOR
opcoes = Options()
opcoes.add_argument("--start-maximized")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)
espera = WebDriverWait(navegador, 15)
# endregion CONFIGURAÇÃO DO NAVEGADOR

# =====================================================================
# ETAPA 1: LOGIN NO PORTAL
# =====================================================================
# region LOGUIM NO PORTAL NOVO
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
# endregion LOGUIM NO PORTAL NOVO

# =====================================================================
# ETAPA 1.5: FIXAR BARRA LATERAL
# =====================================================================
# region FIXANDO A BARRA LATERAL, DENTRO DO PORTAL
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
# endregion FIXANDO A BARRA LATERAL DENTRO DO PORTAL

# =====================================================================
# ETAPA 1.6: SELECIONAR SOLICITANTE/OPERAÇÃO (AMAZON)
# =====================================================================
# region SELECIONANDO A OPERAÇÃO - AMAZON
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
# endregion SELECIONANDO A OPERAÇÃO

# =====================================================================
# ETAPA 1.7: NAVEGAR PARA EMISSÃO E FILTRAR PENDENTES
# =====================================================================
# region NAVENGANDO ATE EMISSÃO / FILTRANDO AS PENDENTES
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
# endregion NAVEGANDO ATE PENDENTES

# =====================================================================
# VARIÁVEIS GLOBAIS DE CONTROLO DE SESSÃO DO SSW
# =====================================================================
# region VARIAVEIS DE CONTROLE DE EMISSÃO-
numero_nota = 0
aba_portal = navegador.window_handles[0]
ssw_logado = False
aba_principal_ssw = None

# === INTELIGÊNCIA: MEMÓRIA DAS NOTAS TENTADAS ===
indices_notas_processadas = []
# ================================================
# endregion Controle de Seção

# =====================================================================
# LOOP PRINCIPAL - PROCESSA EXATAMENTE 10 NOTAS
# =====================================================================
for numero_nota in range(1, 11):
    print(f"\n{'=' * 60}")
    print(f"PROCESSANDO NOTA #{numero_nota} DE 10")
    print(f"{'=' * 60}")

    # Garante foco no portal
    navegador.switch_to.window(aba_portal)

    # Só atualiza a página e aplica filtros na PRIMEIRA VOLTA (para não perder o estado das linhas)
    if numero_nota == 1:
        navegador.refresh()
        time.sleep(3)
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
    else:
        # Nas voltas seguintes, apenas espera um pouco para a tela estabilizar
        time.sleep(1.5)

    # Busca notas livres ignorando filtro fixo
    xpath_notas_livres = "//tr[.//button[contains(., 'Emitir')]]//button[contains(., 'Emitir')]"
    try:
        botoes_emitir = espera.until(EC.presence_of_all_elements_located((By.XPATH, xpath_notas_livres)))
        if numero_nota == 1:
            print(f"Encontrada(s) {len(botoes_emitir)} nota(s) nesta página.")
    except Exception:
        print("Nenhuma nota encontrada. Encerrando robô.")
        break

    nota_acessada = False
    placa_dinamica = ""
    vrid_limpo = ""
    cnpj_pagador = "FALHOU"
    estado_origem = ""

    # === MAPEAR COLUNA DO FRETE A PAGAR DINAMICAMENTE ===
    print("Mapeando colunas da tabela...")
    index_frete_pagar = 7  # Valor padrão de segurança
    try:
        # Pega todos os cabeçalhos (<th>) da tabela
        cabecalhos = espera.until(EC.presence_of_all_elements_located((By.XPATH, "//thead//th")))
        for i, th in enumerate(cabecalhos):
            titulo = th.get_attribute("title") or ""
            texto = th.text or ""
            if "Frete a Pagar" in titulo or "Frete a Pagar" in texto:
                index_frete_pagar = i + 1  # +1 porque o XPath conta a partir do 1
                print(f"✅ Coluna 'Frete a Pagar' detetada automaticamente na posição: {index_frete_pagar}")
                break
    except Exception as e:
        print(f"⚠️ Aviso: Não consegui mapear colunas. Usando coluna {index_frete_pagar} por padrão.")
    # ====================================================

    # ------------------------------------------------------------------
    # TENTA ACESSAR A PRÓXIMA NOTA LIVRE (COM INTELIGÊNCIA DE MEMÓRIA E EXCLUSÃO)
    # ------------------------------------------------------------------
    for index, botao in enumerate(botoes_emitir):

        # 0. VERIFICA SE ESTA NOTA JÁ FOI TENTADA (SE SIM, PULA SILENCIOSAMENTE PARA A DE BAIXO)
        if index in indices_notas_processadas:
            continue

        linha = botao.find_element(By.XPATH, "./ancestor::tr")

        # 1. VERIFICA SE TEM ALERTA DE BORDA VERMELHA
        try:
            alerta_borda = linha.find_elements(By.XPATH,
                                               ".//td[1]//div[contains(@class, 'border-red-500') or contains(@class, 'bg-red-500')]")
            if len(alerta_borda) > 0:
                print(f"🛑 Pulando nota {index + 1}: Alerta de borda/fundo vermelho.")
                continue
        except:
            pass

        # 2. VERIFICA SE TEM O CÍRCULO VERMELHO ANIMADO
        try:
            alerta_circulo = linha.find_elements(By.XPATH, ".//div[contains(@class, 'animate-pulse')]")
            if len(alerta_circulo) > 0:
                print(f"🔴 Pulando nota {index + 1}: Círculo vermelho de atenção detetado.")
                continue
        except:
            pass

        # 3. VERIFICA SE ESTÁ OCUPADA (TEM NOME PREENCHIDO)
        try:
            span_nome = linha.find_element(By.XPATH, ".//td[1]//span[contains(@class, 'truncate')]")
            nome_emitente = span_nome.text.strip()
            if nome_emitente != "":
                print(f"⏭️ Pulando nota {index + 1}: Ocupada por '{nome_emitente}'.")
                continue
        except:
            pass

        # 4. VERIFICA A COLUNA "FRETE A PAGAR" (COM ÍNDICE DINÂMICO)
        try:
            celula_frete = linha.find_element(By.XPATH, f"./td[{index_frete_pagar}]")
            texto_frete = celula_frete.text.strip()

            # 4.1 Verifica se a PRÓPRIA coluna do frete está com borda/fundo vermelho
            alerta_frete = celula_frete.find_elements(By.XPATH,
                                                      ".//*[contains(@class, 'bg-red-500') or contains(@class, 'border-red-500') or contains(@class, 'text-red-500')]")
            if len(alerta_frete) > 0:
                print(f"🔴💰 Pulando nota {index + 1}: Alerta vermelho direto na coluna do Frete a Pagar.")
                continue

            # 4.2 Verifica se o frete é um travessão (—), vazio ou zero
            if texto_frete in ["—", "-", "", "0", "0,00"]:
                print(f"📉💰 Pulando nota {index + 1}: Frete a Pagar está vazio/zerado ('{texto_frete}').")
                continue

            # 4.3 Se tiver R$, converte para número e verifica se é <= 1
            if "R$" in texto_frete:
                texto_limpo = texto_frete.replace("R$", "").replace(".", "").replace(",", ".").strip()
                if texto_limpo != "":
                    valor_frete = float(texto_limpo)
                    if valor_frete <= 1.0:
                        print(f"📉💰 Pulando nota {index + 1}: Valor do frete é R$ {valor_frete:.2f} (<= 1).")
                        continue
        except Exception:
            pass

        # 5. EXTRAIR O ESTADO DE ORIGEM E DESTINO (COM REGRA DO NORDESTE) - Se passa no Nordeste. Descarta!
        try:
            # 5.1 Extrai o Estado de Origem (Coluna 4)
            texto_origem = linha.find_element(By.XPATH, ".//td[4]").text
            linha_origem = texto_origem.split('\n')[0]
            if " - " in linha_origem:
                estado_origem = linha_origem.split(" - ")[-1].strip()[:2].upper()
            else:
                estado_origem = ""

            # 5.2 Extrai o Estado de Destino (Coluna 5)
            texto_destino = linha.find_element(By.XPATH, ".//td[5]").text
            linha_destino = texto_destino.split('\n')[0]
            if " - " in linha_destino:
                estado_destino = linha_destino.split(" - ")[-1].strip()[:2].upper()
            else:
                estado_destino = ""

            # 5.3 REGRA DE EXCLUSÃO DO NORDESTE
            estados_nordeste = ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]

            # Se a origem OU o destino estiverem na lista do Nordeste, o robô pula a nota
            if estado_origem in estados_nordeste or estado_destino in estados_nordeste:
                print(
                    f"🌵 Pulando nota {index + 1}: A rota entra ou sai do Nordeste ({estado_origem} -> {estado_destino}).")
                continue

            print(f"📍 Rota detetada e permitida: {estado_origem} -> {estado_destino}")

        except Exception:
            estado_origem = ""
            estado_destino = ""

        # 6. SE PASSOU POR TODOS OS TESTES, A NOTA ESTÁ LIVRE E VÁLIDA!
        print(f"✅ Nota {index + 1} está OK! Acessando...")

        # Grava na memória que já tentámos esta linha, para não voltar a ela na próxima volta do loop!
        indices_notas_processadas.append(index)

        navegador.execute_script("arguments[0].click();", botao)
        time.sleep(2)

        # Trata pop-up de rota já atribuída que pode aparecer ao clicar
        if navegador.find_elements(By.XPATH, "//*[contains(text(), 'Rota já atribuída')]"):
            navegador.find_element(By.XPATH, "//button[contains(., 'Entendi')]").click()
            time.sleep(1)
            continue

        # Confirma que abriu a tela de emissão da nota
        if navegador.find_elements(By.XPATH, "//*[contains(text(), 'Anexar Documentos de Emissão')]"):
            nota_acessada = True

            # -----------------------------------------------------
            # EXTRAINDO VRID E PLACA DO PORTAL
            # -----------------------------------------------------
            time.sleep(1)

            # 1. Extrai o VRID (Garantindo que pega o pop-up ativo mais recente)
            try:
                elementos_vrid = espera.until(EC.presence_of_all_elements_located((
                    By.XPATH, "//*[contains(text(), 'ID: ')]"
                )))
                vrid_limpo = elementos_vrid[-1].text.replace("ID:", "").strip()
                print(f"🎯 VRID extraído: {vrid_limpo}")
            except Exception as e:
                print("Aviso: Não consegui extrair o VRID do portal.")
                vrid_limpo = ""

            # 2. Extrai a PLACA dinamicamente
            try:
                time.sleep(2)
                xpath_placa = "//span[text()='Placas']/following-sibling::div//span[contains(@class, 'truncate')]"
                elementos_placa = espera.until(EC.presence_of_all_elements_located((By.XPATH, xpath_placa)))
                elemento_alvo = elementos_placa[0]

                placa_dinamica = elemento_alvo.get_attribute("title")
                if not placa_dinamica:
                    placa_dinamica = elemento_alvo.text

                placa_dinamica = placa_dinamica.split('\n')[0].split('-')[0].strip()


                if placa_dinamica == "":
                    print("⚠️ Aviso: O campo de placa foi encontrado, mas estava VAZIO no portal.")
                else:
                    print(f"🎯 Placa extraída com sucesso: {placa_dinamica}")

            except Exception as erro_tecnico:
                print(f"⚠️ Aviso: Não consegui extrair a placa do portal. Motivo: {type(erro_tecnico).__name__}")
                placa_dinamica = ""

            break

    # ------------------------------------------------------------------
    # ETAPA 3: ABRIR SSW E FAZER LOGIN (OU REAPROVEITAR ABA EXISTENTE)
    # ------------------------------------------------------------------
    if not ssw_logado:
        print("Abrindo SSW em nova aba...")
        navegador.execute_script("window.open('');")
        aba_principal_ssw = navegador.window_handles[-1]
        navegador.switch_to.window(aba_principal_ssw)
        navegador.get("https://sistema.ssw.inf.br/")
        time.sleep(3)

        print("Logando no SSW...")
        navegador.find_element(By.ID, '1').send_keys(credenciais.SSW_DOMINIO)
        navegador.find_element(By.ID, '2').send_keys(credenciais.SSW_CPF)
        navegador.find_element(By.ID, '3').send_keys(credenciais.SSW_USUARIO)
        navegador.find_element(By.ID, '4').send_keys(credenciais.SSW_SENHA)
        navegador.find_element(By.ID, "5").click()

        time.sleep(2)
        print("✅ Login SSW Realizado!")
        ssw_logado = True
    else:
        print("SSW já está logado! Voltando para o separador e regressando ao menu inicial...")
        navegador.switch_to.window(aba_principal_ssw)
        time.sleep(3)

    # ------------------------------------------------------------------
    # ETAPA 4: TELA 071 (DINÂMICO)
    # ------------------------------------------------------------------
    print("Indo para a tela 71...")
    campo_unidade = espera.until(EC.element_to_be_clickable((By.ID, "2")))
    campo_unidade.click()
    campo_unidade.send_keys(Keys.CONTROL, "a")
    campo_unidade.send_keys(Keys.BACKSPACE)

    # Aplica a regra ESTADO + 'E'
    unidade_ssw = f"{estado_origem}E"
    print(f"Preenchendo Unidade SSW com: {unidade_ssw}")
    campo_unidade.send_keys(unidade_ssw)
    time.sleep(1)

    janelas_antes_71 = navegador.window_handles

    campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
    campo_opcao.click()
    campo_opcao.send_keys(Keys.CONTROL, "a")
    campo_opcao.send_keys(Keys.BACKSPACE)
    campo_opcao.send_keys("71")
    time.sleep(1)
    campo_opcao.send_keys(Keys.ENTER)

    print("Aguardando o pop-up da tela 71 abrir...")
    espera.until(EC.number_of_windows_to_be(len(janelas_antes_71) + 1))

    aba_nova_71 = [j for j in navegador.window_handles if j not in janelas_antes_71][0]
    navegador.switch_to.window(aba_nova_71)
    navegador.maximize_window()
    print("✅ Tela 71 aberta com sucesso!")

    # ------------------------------------------------------------------
    # ETAPA 5: PREENCHER TELA 071 E PESQUISAR NF (COM INTELIGÊNCIA HÍBRIDA)
    # ------------------------------------------------------------------
    data_retroativa = (datetime.now() - timedelta(days=3)).strftime("%d%m%y")
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

    # Guarda o estado das janelas ANTES do ENTER
    janelas_antes_pesquisa_vrid = navegador.window_handles

    campo_packing_list.send_keys(vrid_limpo)
    time.sleep(1)
    campo_packing_list.send_keys(Keys.ENTER)

    print("Aguardando resposta do SSW (Nova janela de lista ou Erro '7. OK')...")

    # === INTELIGÊNCIA: VERIFICAR ERRO OU SUCESSO EM TEMPO REAL ===
    tempo_limite = time.time() + 60
    nota_sem_nf = False
    sucesso_janela = False

    while time.time() < tempo_limite:

        try:

            botoes_erro = navegador.find_elements(By.XPATH,
                                                  "//a[@id='0' or contains(text(), '7. OK') or contains(text(), '7.')]")
            for btn in botoes_erro:
                if btn.is_displayed():
                    navegador.execute_script("arguments[0].click();", btn)
                    print(f"⚠️ AVISO: O SSW recusou o VRID '{vrid_limpo}'. Pop-up de erro fechado!")
                    nota_sem_nf = True
                    break
            if nota_sem_nf:
                break
        except Exception:
            pass


        if len(navegador.window_handles) > len(janelas_antes_pesquisa_vrid):
            sucesso_janela = True
            break

        time.sleep(1)

    # =================================================================
    # FLUXO DE ABORTO: SE A NOTA NÃO TIVER NF OU DER TIMEOUT
    # =================================================================
    if nota_sem_nf or not sucesso_janela:
        if not sucesso_janela and not nota_sem_nf:
            print("⚠️ TIMEOUT: O SSW não respondeu. Abortando esta nota por segurança.")

        print("Voltando ao portal para ignorar esta nota e passar à próxima...")

        # Fecha abas residuais da Tela 71 e outras, deixando só o Portal e o Menu do SSW
        for handle in list(navegador.window_handles):
            if handle != aba_portal and handle != aba_principal_ssw:
                navegador.switch_to.window(handle)
                navegador.close()
                time.sleep(0.5)

        # Volta ao portal
        navegador.switch_to.window(aba_portal)
        time.sleep(2)

        # Tenta fechar o modal aberto no portal
        try:
            botao_fechar_nota = navegador.find_element(By.XPATH,
                                                       "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
            navegador.execute_script("arguments[0].click();", botao_fechar_nota)
            print("✅ Pop-up da nota no portal fechado.")
        except:
            pass

        print("⏭️ Saltando para a próxima nota do loop...")
        continue  # Comando MÁGICO: Volta para o início do loop (for numero_nota...) e pega a próxima nota!

    # =================================================================
    # FLUXO NORMAL: SE A NOTA TIVER NF (ABRIU A JANELA)
    # =================================================================
    print("✅ O SSW aceitou o VRID. Focando na janela de Lista...")
    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()
    # ------------------------------------------------------------------
    # ETAPA 6: EXTRAIR CNPJ DA NOTA (COM VERIFICAÇÃO "AMAZON")
    # ------------------------------------------------------------------

    print("Aguardando a janela com a lista de notas carregar...")
    time.sleep(5)
    print("Procurando a aba correta da Lista...")
    aba_lista = None

    for aba in navegador.window_handles:
        navegador.switch_to.window(aba)
        if "> Lista" in navegador.title:
            print("✅ Foco na Janela da Lista!")
            aba_lista = aba
            break

    if aba_lista is None:
        raise Exception("Não foi possível encontrar a janela '> Lista'.")

    navegador.maximize_window()
    time.sleep(3)

    linhas_notas = navegador.find_elements(By.XPATH, "//tr[@rid]//a[contains(@class, 'sra2')]")
    quantidade_notas = len(linhas_notas)
    print(f"Total de notas para analisar na lista: {quantidade_notas}")

    cnpj_pagador = "FALHOU"

    for i in range(quantidade_notas):
        janelas_antes = navegador.window_handles

        print(f"Clicando na nota da linha {i + 1}...")
        primeira_nota = espera.until(EC.presence_of_element_located((
            By.XPATH, f"//tr[@rid='{i}']//a[contains(@class, 'sra2')]"
        )))
        navegador.execute_script("arguments[0].click();", primeira_nota)

        espera.until(EC.number_of_windows_to_be(len(janelas_antes) + 1))
        janelas_depois = navegador.window_handles
        aba_nova = [j for j in janelas_depois if j not in janelas_antes][0]

        navegador.switch_to.window(aba_nova)
        navegador.maximize_window()
        time.sleep(3)

        print("Extraindo e analisando o CNPJ do Pagador...")
        try:
            elemento_pagador = espera.until(EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(text(), 'Pagador:')]/following-sibling::div[@class='data']"
            )))
            texto_pagador = elemento_pagador.text.strip()
            print(f"Texto extraído: '{texto_pagador}'")

            if "-" in texto_pagador:
                partes = texto_pagador.split("-", 1)
                nome_pagador = partes[1].strip().upper()

                if "AMAZON" in nome_pagador:
                    cnpj_pagador = partes[0].strip()
                    print(f"✅ Sucesso! Pagador AMAZON confirmado. CNPJ extraído: {cnpj_pagador}")
                    break
                else:
                    print(f"⏭️ Ignorando nota. O pagador não é Amazon (Encontrado: {nome_pagador}).")
            else:
                print("⏭️ Ignorando nota. Formato inesperado (sem traço).")

        except Exception as e:
            print("Aviso: Não consegui extrair o CNPJ desta nota.")

        print("Fechando detalhes desta nota e testando a próxima...")
        navegador.close()
        navegador.switch_to.window(aba_lista)
        time.sleep(8)

    # ------------------------------------------------------------------
    # ETAPA 7: FECHAR ABAS EXTRAS E IR PARA TELA 6
    # ------------------------------------------------------------------
    print("Limpando janelas e voltando ao Menu...")
    for handle in list(navegador.window_handles):
        if handle != aba_portal and handle != aba_principal_ssw:
            navegador.switch_to.window(handle)
            navegador.close()
            time.sleep(1)

    navegador.switch_to.window(aba_principal_ssw)

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
    campo_merc = espera.until(EC.element_to_be_clickable((By.ID, "cod_merc")))
    campo_merc.click()
    campo_merc.clear()
    time.sleep(1)
    campo_merc.send_keys("1")
    time.sleep(1)

    # print("Inserindo Tipo de mercadoria novamente....")
    # campo_tab = espera.until(EC.presence_of_element_located((By.ID, "cod_merc")))
    # campo_tab.click()
    # campo_tab.send_keys(Keys.CONTROL, "a")
    # campo_tab.send_keys(Keys.BACKSPACE)
    # campo_tab.send_keys("1")
    # time.sleep(2)

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

    print("Inserindo Tipo de mercadoria novamente....")
    campo_tab = espera.until(EC.presence_of_element_located((By.ID, "cod_merc")))
    campo_tab.click()
    campo_tab.send_keys(Keys.CONTROL, "a")
    campo_tab.send_keys(Keys.BACKSPACE)
    campo_tab.send_keys("1")
    time.sleep(2)

    # ------------------------------------------------------------------
    # ETAPA 10: CLICAR EM APONTAR NFs (COM INTELIGÊNCIA HÍBRIDA)
    # ------------------------------------------------------------------
    print("Clicando em 'Apontar NFs'...")
    janelas_antes_apontar = navegador.window_handles
    botao_apontar = espera.until(EC.presence_of_element_located((By.ID, "lnk_apontar")))
    navegador.execute_script("arguments[0].click();", botao_apontar)
    print("✅ 'Apontar NFs' clicado!")

    print("Aguardando resposta do SSW (Nova janela de apontamento ou pop-up de Aviso)...")

    # === INTELIGÊNCIA HÍBRIDA: VERIFICAR ERRO OU SUCESSO ===
    tempo_limite = time.time() + 55  # Espera até 15 segundos
    sem_notas_apontar = False
    sucesso_janela_apontar = False
    time.sleep(10)

    while time.time() < tempo_limite:
        # 1. Verifica se o SSW deitou pop-up de Erro (7. OK) dizendo que não há NFs
        try:
            xpath_erro = "//a[@id='0' or contains(text(), '7. OK') or contains(text(), '7.')]"
            botoes_erro = navegador.find_elements(By.XPATH, xpath_erro)
            for btn in botoes_erro:
                if btn.is_displayed():
                    navegador.execute_script("arguments[0].click();", btn)
                    print("⚠️ AVISO: SSW informou que não há notas para apontar! Pop-up fechado.")
                    sem_notas_apontar = True
                    time.sleap()
                    break
            if sem_notas_apontar:
                break
        except Exception:
            pass

        # 2. Verifica se o SSW abriu a nova janela com a lista de notas (Sucesso)
        if len(navegador.window_handles) > len(janelas_antes_apontar):
            sucesso_janela_apontar = True
            break

        time.sleep(1)

    # =================================================================
    # FLUXO DE ABORTO: SE NÃO HOUVER NOTAS PARA APONTAR
    # =================================================================
    if sem_notas_apontar or not sucesso_janela_apontar:
        if not sucesso_janela_apontar and not sem_notas_apontar:
            print("⚠️ TIMEOUT: Janela de apontar NFs não abriu e nenhum aviso foi dado.")

        print("Limpando janelas e voltando ao portal para processar a próxima nota...")

        # Fecha tudo exceto o Portal e a tela principal do SSW
        for handle in list(navegador.window_handles):
            if handle != aba_portal and handle != aba_principal_ssw:
                navegador.switch_to.window(handle)
                navegador.close()
                time.sleep(0.5)

        # Volta ao portal
        navegador.switch_to.window(aba_portal)
        time.sleep(2)

        # Tenta fechar o modal aberto da Amazon no portal
        try:
            botao_fechar_nota = navegador.find_element(By.XPATH,
                                                       "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
            navegador.execute_script("arguments[0].click();", botao_fechar_nota)
            print("✅ Pop-up da nota no portal fechado.")
            time.sleep(15)
        except:
            pass

        print("⏭️ Saltando para a próxima nota do loop...")
        continue  # Comando que aborta esta nota e volta para o início do loop!

    # =================================================================
    # FLUXO NORMAL: SE ABRIU A JANELA PARA APONTAR NOTAS
    # =================================================================
    for handle in navegador.window_handles:
        if handle not in janelas_antes_apontar:
            navegador.switch_to.window(handle)
            navegador.maximize_window()
            print("✅ Janela de Apontar NFs aberta com sucesso!")
            break

    # Pausa para garantir que a grelha de notas carrega completamente antes da Etapa 11
    time.sleep(35)

    # ------------------------------------------------------------------
    # ETAPA 11: SELEÇÃO E ENVIO (ÚNICA VEZ)
    # ------------------------------------------------------------------
    print("\n--- INICIANDO SELEÇÃO E ENVIO ---")

    print("Selecionando todas as paginas...")
    checkbox_todas = WebDriverWait(navegador, 35).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@class='baselnk' and contains(text(), 'Marcar')]")))
    navegador.execute_script("arguments[0].click();", checkbox_todas)
    print("✅ Todas as paginas selecionadas!")
    time.sleep(10)

    print("Dando scroll até o final da página...")
    navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)

    print("Clicando na setinha de avançar...")
    try:
        botao_avancar = WebDriverWait(navegador, 45).until(
            EC.element_to_be_clickable((By.XPATH, '(//a[@class="srimglnk" and @accesskey="&"])[1]')))
        navegador.execute_script("arguments[0].click();", botao_avancar)
        print("✅ Setinha clicada!")
    except Exception:
        print("ℹ Setinha não encontrada.")
    time.sleep(40)

    print("Clicando em Continuar no popup...")
    try:
        btn_continuar = WebDriverWait(navegador, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@class='dialog' and contains(text(), 'Continuar')]")))
        navegador.execute_script("arguments[0].click();", btn_continuar)
        print("✅ Continuar clicado!")
    except Exception:
        print("ℹ Popup Continuar não encontrado.")
    time.sleep(18)

    print("Aguardando popup 7.OK...")
    time.sleep(8)
    ok_clicado = False

    try:
        # Varre as janelas abertas para ter a certeza de que acha o 7.OK onde ele estiver
        for handle in navegador.window_handles:
            navegador.switch_to.window(handle)
            xpath_popup = "//a[contains(text(), '7. OK') or contains(text(), '7.')] | //div[@id='errormsg']//a"
            elementos = navegador.find_elements(By.XPATH, xpath_popup)

            if len(elementos) > 0:
                navegador.execute_script("arguments[0].click();", elementos[0])
                print("✅ 7.OK clicado com sucesso!")
                ok_clicado = True
                break

        if not ok_clicado:
            print("⚠️ Popup 7.OK não apareceu no tempo esperado.")

    except Exception as e:
        print(f"⚠️ Erro ao procurar popup 7.OK: {e}")

    time.sleep(5)
    print(f"\n✅ Nota #{numero_nota} ({vrid_limpo}). Lançamento concluído com sucesso!")

    # ------------------------------------------------------------------
    # FECHAR TODAS AS JANELAS EXTRAS E VOLTAR AO PORTAL
    # ------------------------------------------------------------------
    print("Fechando janelas extras e voltando ao portal...")

    # Mantém apenas o Portal (aba_portal) e o SSW (aba_principal_ssw)
    for handle in list(navegador.window_handles):
        if handle != aba_portal and handle != aba_principal_ssw:
            navegador.switch_to.window(handle)
            navegador.close()
            time.sleep(1)

    navegador.switch_to.window(aba_portal)
    time.sleep(3)
    print("✅ De volta ao portal! Buscando próxima nota...")

# =====================================================================
# FIM DO LOOP
# =====================================================================
print("\n✅ Robô finalizado! Todas as notas foram processadas.")
time.sleep(10)