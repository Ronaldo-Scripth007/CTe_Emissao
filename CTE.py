import time
import os
import re
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

print("Iniciando Robô de Emissão de CTE.")

# =====================================================================
# CONFIGURAÇÃO DO NAVEGADOR
# =====================================================================
# region Conf NAVEGADOR
opcoes = Options()
opcoes.add_argument("--start-maximized")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)
espera = WebDriverWait(navegador, 15)
# endregion

# =====================================================================
# ETAPA 1: LOGIN NO PORTAL DEDICADO
# =====================================================================
# region LOGUIM NO PORTAL
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
# endregion

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
# VARIÁVEIS GLOBAIS DE CONTROLO DE SESSÃO DO SSW
# =====================================================================
# region Cntrl Seção SSW
numero_nota = 0
aba_portal = navegador.window_handles[0]
ssw_logado = False
aba_principal_ssw = None

# -- INTELIGÊNCIA: MEMÓRIA DAS NOTAS E FILA 156 ---
indices_notas_processadas = []
lotes_pendentes_156 = []
# endregion
# ==========================================================

# =====================================================================
# LOOP PRINCIPAL - PROCESSA EXATAMENTE 3 NOTAS
# =====================================================================
for numero_nota in range(1,4):
    print(f"\n{'=' * 60}")
    print(f"PROCESSANDO NOTA #{numero_nota} DE 0")
    print(f"{'=' * 60}")

    # Garante foco no portal
    navegador.switch_to.window(aba_portal)

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
        time.sleep(1.5)

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
    cnpj_pagador = "FALHOU" ##
    estado_origem = ""
    cidade_origem = ""
    estado_destino = ""
    cidade_destino = ""
    data_previsao = ""
    hora_previsao = ""
    valor_pagar = ""

    print("Mapeando colunas da tabela...")
    index_frete_pagar = 7
    try:
        cabecalhos = espera.until(EC.presence_of_all_elements_located((By.XPATH, "//thead//th")))
        for i, th in enumerate(cabecalhos):
            titulo = th.get_attribute("title") or ""
            texto = th.text or ""
            if "Frete a Pagar" in titulo or "Frete a Pagar" in texto:
                index_frete_pagar = i + 1
                print(f"✅ Coluna 'Frete a Pagar' detetada automaticamente na posição: {index_frete_pagar}")
                break
    except Exception as e:
        print(f"⚠️ Aviso: Não consegui mapear colunas. Usando coluna {index_frete_pagar} por padrão.")

    # ------------------------------------------------------------------
    # TENTA ACESSAR A PRÓXIMA NOTA LIVRE
    # ------------------------------------------------------------------
    for index, botao in enumerate(botoes_emitir):

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

        # 1.5. VERIFICA SE A LINHA INTEIRA ESTÁ VERMELHA
        try:
            classes_da_linha = linha.get_attribute("class") or ""
            if "text-red" in classes_da_linha:
                print(f"🩸 Pulando nota {index + 1}: A linha inteira está com texto vermelho.")
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

        # 3. VERIFICA SE ESTÁ OCUPADA
        try:
            span_nome = linha.find_element(By.XPATH, ".//td[1]//span[contains(@class, 'truncate')]")
            nome_emitente = span_nome.text.strip()
            if nome_emitente != "":
                print(f"⏭️ Pulando nota {index + 1}: Ocupada por '{nome_emitente}'.")
                continue
        except:
            pass

        # 4. VERIFICA A COLUNA "FRETE A PAGAR"
        try:
            # Busca TODAS as células da linha que contêm o texto 'R$'
            celulas_dinheiro = linha.find_elements(By.XPATH, ".//td[contains(., 'R$')]")

            if len(celulas_dinheiro) >= 2:
                # O índice 0 é o Frete a Receber, o índice 1 é o Frete a Pagar!
                celula_frete = celulas_dinheiro[1]
            elif len(celulas_dinheiro) == 1:
                # Caso excecional onde só exista um R$ na linha
                celula_frete = celulas_dinheiro[0]
            else:
                print(f"📉💰 Pulando nota {index + 1}: Não encontrei nenhum valor em R$ na linha.")
                continue

            # Extrai o texto e limpa o espaço fantasma do HTML (\xa0 ou &nbsp;)
            texto_frete = celula_frete.get_attribute("innerText").replace("\xa0", " ").strip()

            # 4.1 Verifica se a PRÓPRIA coluna do frete está com alerta vermelho
            alerta_frete = celula_frete.find_elements(By.XPATH,
                                                      ".//*[contains(@class, 'bg-red-500') or contains(@class, 'border-red-500') or contains(@class, 'text-red-500')]")
            if len(alerta_frete) > 0:
                print(f"🔴💰 Pulando nota {index + 1}: Alerta vermelho direto na coluna do Frete a Pagar.")
                continue

            # 4.2 Verifica se o frete é um travessão (—), vazio ou zero
            if texto_frete in ["—", "-", "", "0", "0,00", "R$ 0,00", "R$ 0"]:
                print(f"📉💰 Pulando nota {index + 1}: Frete a Pagar está vazio/zerado ('{texto_frete}').")
                continue

            # 4.3 Limpa o R$ e converte para número para validar se é > 1.00
            texto_limpo = texto_frete.replace("R$", "").replace(".", "").replace(",", ".").strip()
            if texto_limpo != "":
                valor_frete = float(texto_limpo)
                if valor_frete <= 1.0:
                    print(f"📉💰 Pulando nota {index + 1}: Valor do frete é muito baixo (R$ {valor_frete:.2f}).")
                    continue

        except Exception as e:
            print(f"⚠️ Erro ao analisar o Frete a Pagar da nota {index + 1}. Pulando.")
            continue

        # =====================================================================
        # 5. EXTRAIR O ESTADO DE ORIGEM E DESTINO (ROBUSTO)
        # =====================================================================
        try:
            celula_origem = linha.find_element(By.XPATH, ".//td[4]")
            texto_origem = celula_origem.text
            if not texto_origem or texto_origem == "":
                texto_origem = celula_origem.get_attribute("innerText")

            linha_origem = texto_origem.split('\n')[0].strip().replace("...", "").strip()
            if "-" in linha_origem:
                estado_origem = linha_origem.split("-")[-1].strip()[:2].upper()
                cidade_origem = linha_origem.split("-")[0].strip()
            elif "/" in linha_origem:
                estado_origem = linha_origem.split("/")[-1].strip()[:2].upper()
                cidade_origem = linha_origem.split("/")[0].strip()
            else:
                partes = linha_origem.split()
                if len(partes) > 1 and len(partes[-1]) == 2:
                    estado_origem = partes[-1].upper()
                    cidade_origem = " ".join(partes[:-1]).strip()
                else:
                    estado_origem = "MG"
                    cidade_origem = linha_origem
        except Exception as e:
            print(f"⚠️ Erro ao extrair Origem: {e}")
            estado_origem = ""

        try:
            celula_destino = linha.find_element(By.XPATH, ".//td[5]")
            texto_destino = celula_destino.text
            if not texto_destino or texto_destino == "":
                texto_destino = celula_destino.get_attribute("innerText")

            linha_destino = texto_destino.split('\n')[0].strip().replace("...", "").strip()
            if "-" in linha_destino:
                estado_destino = linha_destino.split("-")[-1].strip()[:2].upper()
                cidade_destino = linha_destino.split("-")[0].strip()
            elif "/" in linha_destino:
                estado_destino = linha_destino.split("/")[-1].strip()[:2].upper()
                cidade_destino = linha_destino.split("/")[0].strip()
            else:
                partes_dest = linha_destino.split()
                if len(partes_dest) > 1 and len(partes_dest[-1]) == 2:
                    estado_destino = partes_dest[-1].upper()
                    cidade_destino = " ".join(partes_dest[:-1]).strip()
                else:
                    estado_destino = "MG"
                    cidade_destino = linha_destino

            try:
                linha_data_hora = texto_destino.split('\n')[1]
                data_bruta = linha_data_hora.split(' - ')[0].strip()
                partes_data = data_bruta.split('/')
                data_previsao = f"{partes_data[0]}{partes_data[1]}{partes_data[2][-2:]}"
                hora_previsao = linha_data_hora.split(' - ')[1].strip().replace(":", "")
            except:
                pass
        except Exception as e:
            print(f"⚠️ Erro ao extrair Destino: {e}")
            estado_destino = ""

        try:
            celulas_valor = linha.find_elements(By.XPATH, ".//td[contains(text(), 'R$')]")
            if len(celulas_valor) > 0:
                texto_valor = celulas_valor[-1].text
            else:
                texto_valor = "0,00"
            valor_pagar = texto_valor.replace("R$", "").replace(".", "").strip()
        except:
            valor_pagar = "0,00"

        # REGRA DE EXCLUSIVIDADE: APENAS MG
        if estado_origem != "MG" or estado_destino != "MG":
            print(f"🚫 Pulando nota {index + 1}: A rota não é 100% MG ({estado_origem} -> {estado_destino}).")
            continue

        print(
            f"📍 Rota detetada e permitida (100% MG): {cidade_origem}-{estado_origem} -> {cidade_destino}-{estado_destino}")
        print(f"✅ Nota {index + 1} está OK! Acessando...")
        indices_notas_processadas.append(index)

        navegador.execute_script("arguments[0].click();", botao)
        time.sleep(2)

        if navegador.find_elements(By.XPATH, "//*[contains(text(), 'Rota já atribuída')]"):
            navegador.find_element(By.XPATH, "//button[contains(., 'Entendi')]").click()
            time.sleep(1)
            continue

        if navegador.find_elements(By.XPATH, "//*[contains(text(), 'Anexar Documentos de Emissão')]"):
            nota_acessada = True
            time.sleep(1)
            try:
                elementos_vrid = espera.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'ID: ')]")))
                vrid_limpo = elementos_vrid[-1].text.replace("ID:", "").strip()
                print(f"🎯 VRID extraído: {vrid_limpo}")
            except Exception as e:
                print("Aviso: Não consegui extrair o VRID do portal.")
                vrid_limpo = ""

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
                placa_dinamica = ""

            try:
                celula_frete = linha.find_element(By.XPATH, f"./td[{index_frete_pagar}]")
                texto_valor = celula_frete.text.strip()
                valor_limpo = texto_valor.replace("R$", "").replace("\xa0", "").replace(".", "").replace(",",
                                                                                                         ".").strip()
                if not valor_limpo or float(valor_limpo) <= 0:
                    print(f"⚠️ AVISO: Valor zerado confirmado dentro da nota. Pulando.")
                    continue
                valor_pagar = texto_valor.replace("R$", "").replace("\xa0", "").replace(".", "").strip()
                print(f"💰 Valor confirmado: {valor_pagar}")
            except Exception as e:
                continue

            pagamento_extraido = "100%"
            pix_extraido = ""
            try:
                try:
                    pagamento_extraido = navegador.find_element(By.XPATH,
                                                                "//*[contains(text(), 'PAGAMENTO')]/following-sibling::*[1]").text.strip()
                except:
                    pass
                try:
                    pix_extraido = navegador.find_element(By.XPATH,
                                                          "//*[text()='PIX' or contains(text(), 'PIX')]/following-sibling::*[1]").text.strip()
                except:
                    pass
                if not pix_extraido:
                    try:
                        bloco_pix = navegador.find_element(By.XPATH,
                                                           "//*[text()='PIX' or contains(text(), 'PIX')]/..").text
                        pix_extraido = \
                        bloco_pix.replace("PIX", "").replace("DADOS PROPRIETÁRIO", "").strip().split("\n")[0]
                    except:
                        pass
            except:
                pass

            if estado_origem == "MG" and estado_destino == "MG":
                print("\n" + "=" * 40)
                print("📊 RESUMO DA NOTA CAPTURADA")
                print("=" * 40)
                print(f"🛻 PLACA:    {placa_dinamica}")
                print(f"📌 VRID:     {vrid_limpo}")
                print(f"📍 ROTA:     {estado_origem} -> {estado_destino}")
                print(f"💰 LIMPO:    {valor_limpo}")
                print(f"💵 PAGAR:    R$ {valor_pagar}")
                print("=" * 40 + "\n")
            # ================================
            break

    # =========================================================================
    # BARREIRA DE SEGURANÇA: NENHUMA NOTA VÁLIDA NA PÁGINA
    # =========================================================================
    if not nota_acessada:
        print("\n⚠️ Não encontrei notas a ser lançadas no portal.")
        print("Encerrando a busca de novas notas...")
        break
    # =========================================================================

    # ------------------------------------------------------------------
    # ETAPA 3: ABRIR SSW E FAZER LOGIN
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
        print("SSW já logado! Regressando ao menu inicial...")
        navegador.switch_to.window(aba_principal_ssw)
        time.sleep(3)

    # ------------------------------------------------------------------
    # ETAPA 4: TELA 071
    # ------------------------------------------------------------------
    print("Indo para a tela 71...")
    campo_unidade = espera.until(EC.element_to_be_clickable((By.ID, "2")))
    campo_unidade.click()
    campo_unidade.send_keys(Keys.CONTROL, "a")
    campo_unidade.send_keys(Keys.BACKSPACE)
    time.sleep(1.5)

    if estado_origem == "":
        print("⚠️ Aviso: Forçando a usar o 'MG' estático")
        estado_origem = "MG"

    unidade_ssw = f"{estado_origem}E"
    print(f"Preenchendo Unidade SSW com: {unidade_ssw}")
    campo_unidade.send_keys(unidade_ssw)
    time.sleep(1.5)

    janelas_antes_71 = navegador.window_handles
    campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
    campo_opcao.click()
    campo_opcao.send_keys(Keys.CONTROL, "a")
    campo_opcao.send_keys(Keys.BACKSPACE)
    campo_opcao.send_keys("71", Keys.ENTER)

    print("Aguardando tela 71...")
    espera.until(EC.number_of_windows_to_be(len(janelas_antes_71) + 1))
    aba_nova_71 = [j for j in navegador.window_handles if j not in janelas_antes_71][0]
    navegador.switch_to.window(aba_nova_71)
    navegador.maximize_window()

    # ------------------------------------------------------------------
    # ETAPA 5: PREENCHER TELA 071 E PESQUISAR NF
    # ------------------------------------------------------------------
    data_retroativa = (datetime.now() - timedelta(days=3)).strftime("%d%m%y")
    campo_data_ini = espera.until(EC.presence_of_element_located((By.ID, "fld_data_ini")))
    campo_data_ini.click()
    campo_data_ini.send_keys(Keys.CONTROL, "a")
    campo_data_ini.send_keys(Keys.BACKSPACE)
    campo_data_ini.send_keys(data_retroativa)
    time.sleep(2)

    campo_packing_list = espera.until(EC.presence_of_element_located((By.ID, "fld_packing_list")))
    campo_packing_list.click()
    campo_packing_list.send_keys(Keys.CONTROL, "a")
    campo_packing_list.send_keys(Keys.BACKSPACE)

    janelas_antes_pesquisa_vrid = navegador.window_handles
    campo_packing_list.send_keys(vrid_limpo)
    time.sleep(1)
    campo_packing_list.send_keys(Keys.ENTER)

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
                    print(f"⚠️ AVISO: Nenhuma nota fiscal encontrada '{vrid_limpo}'. Pop-up fechado!")
                    nota_sem_nf = True
                    break
            if nota_sem_nf: break
        except Exception:
            pass

        if len(navegador.window_handles) > len(janelas_antes_pesquisa_vrid):
            sucesso_janela = True
            break
        time.sleep(1)

    if nota_sem_nf or not sucesso_janela:
        for handle in list(navegador.window_handles):
            if handle != aba_portal and handle != aba_principal_ssw:
                navegador.switch_to.window(handle)
                navegador.close()
                time.sleep(0.5)
        navegador.switch_to.window(aba_portal)
        time.sleep(2)
        try:
            botao_fechar_nota = navegador.find_element(By.XPATH,
                                                       "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
            navegador.execute_script("arguments[0].click();", botao_fechar_nota)
        except:
            pass
        continue

    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()

    # ------------------------------------------------------------------
    # ETAPA 6: EXTRAIR CNPJ DA NOTA
    # ------------------------------------------------------------------
    time.sleep(5)
    aba_lista = None
    for aba in navegador.window_handles:
        navegador.switch_to.window(aba)
        if "> Lista" in navegador.title:
            aba_lista = aba
            break

    if aba_lista is None: raise Exception("Não foi possível encontrar a janela '> Lista'.")
    navegador.maximize_window()
    time.sleep(3)

    linhas_notas = navegador.find_elements(By.XPATH, "//tr[@rid]//a[contains(@class, 'sra2')]")
    quantidade_notas = len(linhas_notas)
    cnpj_pagador = "FALHOU"

    for i in range(quantidade_notas):
        janelas_antes = navegador.window_handles
        primeira_nota = espera.until(
            EC.presence_of_element_located((By.XPATH, f"//tr[@rid='{i}']//a[contains(@class, 'sra2')]")))
        navegador.execute_script("arguments[0].click();", primeira_nota)
        espera.until(EC.number_of_windows_to_be(len(janelas_antes) + 1))

        aba_nova = [j for j in navegador.window_handles if j not in janelas_antes][0]
        navegador.switch_to.window(aba_nova)
        navegador.maximize_window()
        time.sleep(3)

        try:
            elemento_pagador = espera.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Pagador:')]/following-sibling::div[@class='data']")))
            texto_pagador = elemento_pagador.text.strip()
            if "-" in texto_pagador:
                partes = texto_pagador.split("-", 1)
                nome_pagador = partes[1].strip().upper()
                if "AMAZON" in nome_pagador:
                    cnpj_pagador = partes[0].strip()
                    print(f"✅ Pagador AMAZON confirmado. CNPJ: {cnpj_pagador}")
                    break
        except Exception:
            pass

        navegador.close()
        navegador.switch_to.window(aba_lista)
        time.sleep(8)

    for handle in list(navegador.window_handles):
        if handle != aba_portal and handle != aba_principal_ssw:
            navegador.switch_to.window(handle)
            navegador.close()
            time.sleep(1)

    navegador.switch_to.window(aba_principal_ssw)

    campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
    campo_opcao.click()
    campo_opcao.send_keys(Keys.CONTROL, "a")
    campo_opcao.send_keys(Keys.BACKSPACE)
    campo_opcao.send_keys("6", Keys.ENTER)
    time.sleep(5)
    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()

    # ------------------------------------------------------------------
    # ETAPA 8 & 9: PREENCHER FORMULÁRIO TELA 6
    # ------------------------------------------------------------------
    janelas_antes_e = navegador.window_handles
    botao_e = espera.until(EC.presence_of_element_located((By.ID, "link_doc_e")))
    navegador.execute_script("arguments[0].click();", botao_e)
    time.sleep(3)
    if len(navegador.window_handles) > len(janelas_antes_e):
        aba_nova_e = [j for j in navegador.window_handles if j not in janelas_antes_e][0]
        navegador.switch_to.window(aba_nova_e)
        navegador.maximize_window()

    janelas_antes_g = navegador.window_handles
    botao_g = espera.until(EC.presence_of_element_located((By.ID, "link_doc_g")))
    navegador.execute_script("arguments[0].click();", botao_g)
    time.sleep(3)
    if len(navegador.window_handles) > len(janelas_antes_g):
        aba_nova_g = [j for j in navegador.window_handles if j not in janelas_antes_g][0]
        navegador.switch_to.window(aba_nova_g)
        navegador.maximize_window()

    if cnpj_pagador and cnpj_pagador != "FALHOU":
        campo_cnpj = espera.until(EC.presence_of_element_located((By.ID, "cgc_pagador")))
        campo_cnpj.click()
        campo_cnpj.send_keys(Keys.CONTROL, "a")
        campo_cnpj.send_keys(Keys.BACKSPACE)
        campo_cnpj.send_keys(cnpj_pagador)

    data_primeiro_dia = datetime.now().replace(day=1).strftime("%d%m%y")
    campo_data_ini_tela6 = espera.until(EC.presence_of_element_located((By.ID, "data_ini")))
    campo_data_ini_tela6.click()
    campo_data_ini_tela6.send_keys(Keys.CONTROL, "a")
    campo_data_ini_tela6.send_keys(Keys.BACKSPACE)
    campo_data_ini_tela6.send_keys(data_primeiro_dia)
    time.sleep(0.5)

    campo_packing = espera.until(EC.presence_of_element_located((By.ID, "fld_packing")))
    campo_packing.click()
    campo_packing.send_keys(Keys.CONTROL, "a")
    campo_packing.send_keys(Keys.BACKSPACE)
    campo_packing.send_keys(vrid_limpo)
    time.sleep(2)

    placa_veiculo = placa_dinamica if placa_dinamica != "" else "-"
    campo_placa_coleta = espera.until(EC.presence_of_element_located((By.ID, "placa_coleta")))
    campo_placa_coleta.click()
    campo_placa_coleta.send_keys(Keys.CONTROL, "a")
    campo_placa_coleta.send_keys(Keys.BACKSPACE)
    campo_placa_coleta.send_keys(placa_veiculo)
    time.sleep(2)

    campo_merc = espera.until(EC.element_to_be_clickable((By.ID, "cod_merc")))
    campo_merc.click()
    campo_merc.clear()
    time.sleep(4)
    campo_merc.send_keys("1")
    time.sleep(2)

    campo_tab = espera.until(EC.presence_of_element_located((By.ID, "tab_gen")))
    campo_tab.click()
    campo_tab.send_keys(Keys.CONTROL, "a")
    campo_tab.send_keys(Keys.BACKSPACE)
    campo_tab.send_keys("S")
    time.sleep(1)

    campo_placa_prov = espera.until(EC.presence_of_element_located((By.ID, "placa_prov")))
    campo_placa_prov.click()
    campo_placa_prov.send_keys(Keys.CONTROL, "a")
    campo_placa_prov.send_keys(Keys.BACKSPACE)
    campo_placa_prov.send_keys(placa_veiculo)
    time.sleep(2)

    campo_merc = espera.until(EC.presence_of_element_located((By.ID, "cod_merc")))
    campo_merc.click()
    campo_merc.send_keys(Keys.CONTROL, "a")
    campo_merc.send_keys(Keys.BACKSPACE)
    campo_merc.send_keys("1")
    time.sleep(2)

    # ------------------------------------------------------------------
    # ETAPA 10 & 11: APONTAR NFs E ENVIAR
    # ------------------------------------------------------------------
    janelas_antes_apontar = navegador.window_handles
    botao_apontar = espera.until(EC.presence_of_element_located((By.ID, "lnk_apontar")))
    navegador.execute_script("arguments[0].click();", botao_apontar)

    tempo_limite = time.time() + 55
    sem_notas_apontar = False
    sucesso_janela_apontar = False
    time.sleep(10)

    while time.time() < tempo_limite:
        try:
            xpath_erro = "//a[@id='0' or contains(text(), '7. OK') or contains(text(), '7.')]"
            botoes_erro = navegador.find_elements(By.XPATH, xpath_erro)
            for btn in botoes_erro:
                if btn.is_displayed():
                    navegador.execute_script("arguments[0].click();", btn)
                    sem_notas_apontar = True
                    time.sleep(5)
                    break
            if sem_notas_apontar: break
        except Exception:
            pass

        if len(navegador.window_handles) > len(janelas_antes_apontar):
            sucesso_janela_apontar = True
            break
        time.sleep(5)

    if sem_notas_apontar or not sucesso_janela_apontar:
        for handle in list(navegador.window_handles):
            if handle != aba_portal and handle != aba_principal_ssw:
                navegador.switch_to.window(handle)
                navegador.close()
                time.sleep(3)
        navegador.switch_to.window(aba_portal)
        time.sleep(3)
        try:
            botao_fechar_nota = navegador.find_element(By.XPATH,
                                                       "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
            navegador.execute_script("arguments[0].click();", botao_fechar_nota)
        except:
            pass
        continue

    for handle in navegador.window_handles:
        if handle not in janelas_antes_apontar:
            navegador.switch_to.window(handle)
            navegador.maximize_window()
            break

    time.sleep(35)
    checkbox_todas = WebDriverWait(navegador, 35).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@class='baselnk' and contains(text(), 'Marcar')]")))
    navegador.execute_script("arguments[0].click();", checkbox_todas)
    time.sleep(10)

    navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    try:
        botao_avancar = WebDriverWait(navegador, 45).until(
            EC.element_to_be_clickable((By.XPATH, '(//a[@class="srimglnk" and @accesskey="&"])[1]')))
        navegador.execute_script("arguments[0].click();", botao_avancar)
    except Exception:
        pass
    time.sleep(30)

    try:
        btn_continuar = WebDriverWait(navegador, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@class='dialog' and contains(text(), 'Continuar')]")))
        navegador.execute_script("arguments[0].click();", btn_continuar)
    except Exception:
        pass

    print("Aguardando popup 7.OK ou aviso de Fila 156...")
    time.sleep(15)
    ok_clicado = False
    foi_para_fila_156 = False
    numero_sequencia = ""

    try:
        for handle in navegador.window_handles:
            navegador.switch_to.window(handle)
            xpath_popup = "//a[contains(text(), '7. OK') or contains(text(), '7.')] | //div[@id='errormsg']//a"
            elementos = navegador.find_elements(By.XPATH, xpath_popup)

            if len(elementos) > 0:
                texto_tela = navegador.find_element(By.TAG_NAME, "body").text
                if "156" in texto_tela or "lote" in texto_tela.lower() or "processamento" in texto_tela.lower():
                    foi_para_fila_156 = True
                    match = re.search(r'Sequência[^\d]*(\d+)', texto_tela, re.IGNORECASE)
                    if not match: match = re.search(r'(\d{5,8})', texto_tela)
                    if match:
                        numero_sequencia = match.group(1)
                        lotes_pendentes_156.append({"vrid": vrid_limpo, "sequencia": numero_sequencia})
                        print(f"⚠️ CTe enviado para a fila 156! (Sequência: {numero_sequencia})")

                navegador.execute_script("arguments[0].click();", elementos[0])
                print("✅ 7.OK clicado com sucesso!")
                ok_clicado = True
                break
    except Exception as e:
        print(f"⚠️ Erro ao procurar popup 7.OK: {e}")

    # ------------------------------------------------------------------
    # FECHAR JANELAS E ANEXAR CTE (SE NÃO FOI PARA A FILA)
    # ------------------------------------------------------------------
    for handle in list(navegador.window_handles):
        if handle != aba_portal and handle != aba_principal_ssw:
            navegador.switch_to.window(handle)
            navegador.close()
            time.sleep(0.5)

    navegador.switch_to.window(aba_portal)
    time.sleep(3)

    if foi_para_fila_156:
        print(f"⏭️ A nota {vrid_limpo} foi para a 156. Fechando o modal da Amazon para anexar depois...")
        try:
            btn_fechar = navegador.find_element(By.XPATH,
                                                "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
            navegador.execute_script("arguments[0].click();", btn_fechar)
        except:
            pass
        continue

    print("\n--- ANEXANDO CTE NO PORTAL (EMISSÃO DIRETA) ---")
    try:
        xpath_input_cte = "//span[contains(text(), 'CTe')]/following-sibling::input[@type='file']"
        input_cte = espera.until(EC.presence_of_element_located((By.XPATH, xpath_input_cte)))
        input_cte.send_keys(credenciais.CAMINHO_CTE)
        print(f"✅ Arquivo CTe anexado com sucesso para o VRID {vrid_limpo}!")
        time.sleep(6)
        try:
            btn_fechar = navegador.find_element(By.XPATH,
                                                "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
            navegador.execute_script("arguments[0].click();", btn_fechar)
        except:
            pass
    except Exception as e:
        print(f"⚠️ Erro ao anexar o CTE: {e}")

# =====================================================================
# FASE FINAL: VERIFICAÇÃO DA FILA 156  (NOTAS AGUARDANDO)
# =====================================================================
if len(lotes_pendentes_156) > 0:
    print(f"\n{'=' * 60}")
    print(f"🕵️ INICIANDO VERIFICAÇÃO DE {len(lotes_pendentes_156)} LOTES NA FILA 156")
    print(f"{'=' * 60}")

    navegador.switch_to.window(aba_principal_ssw)
    campo_opcao = espera.until(EC.element_to_be_clickable((By.ID, "3")))
    campo_opcao.click()
    campo_opcao.send_keys(Keys.CONTROL, "a")
    campo_opcao.send_keys(Keys.BACKSPACE)
    campo_opcao.send_keys("156", Keys.ENTER)
    time.sleep(5)

    navegador.switch_to.window(navegador.window_handles[-1])
    navegador.maximize_window()
    lotes_concluidos = []

    for tentativa in range(30):
        for lote in lotes_pendentes_156:
            if lote in lotes_concluidos: continue

            try:
                linha_lote = navegador.find_element(By.XPATH, f"//tr[td[1][contains(text(), '{lote['sequencia']}')]]")
                situacao = linha_lote.find_element(By.XPATH, "./td[7]").text.strip().lower()

                if "concluído" in situacao:
                    msg = linha_lote.find_element(By.XPATH, "./td[9]").text.strip()
                    print(f"✅ Lote {lote['sequencia']} (VRID: {lote['vrid']}) finalizado! Mensagem: {msg}")
                    if "sucesso" in msg.lower():
                        print(f"📦 ATENÇÃO: Vá ao portal anexar manualmente o CTe para o VRID {lote['vrid']}.")
                    lotes_concluidos.append(lote)
                elif "erro" in situacao or "rejeitado" in situacao:
                    print(f"❌ Falha crítica no Lote {lote['sequencia']} (VRID: {lote['vrid']}). A SSW rejeitou.")
                    lotes_concluidos.append(lote)
            except:
                pass

        if len(lotes_concluidos) == len(lotes_pendentes_156): break
        time.sleep(30)
        try:
            navegador.execute_script("arguments[0].click();",
                                     navegador.find_element(By.XPATH, "//a[contains(text(), 'Atualizar')]"))
        except:
            navegador.refresh()
        time.sleep(5)

print("\n🏁 FINALIZADO TODO O FLUXO DE EMISSÃO!")