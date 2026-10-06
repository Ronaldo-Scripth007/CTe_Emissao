import time
import unicodedata
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

print("Iniciando Robô de Emissão de CTRB (Tela 72) com Loop e Memória...")

# =====================================================================
# CONFIGURAÇÃO DO NAVEGADOR E VARIÁVEIS GLOBAIS DE MEMÓRIA
# =====================================================================
opcoes = Options()
opcoes.add_argument("--start-maximized")

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico, options=opcoes)
espera = WebDriverWait(navegador, 15)

# === INTELIGÊNCIA: CAIXA DE MEMÓRIAS PARA NOTAS JÁ PROCESSADAS ===
# Guarda tuplos com formato: ("VRID_AQUI", "PLACA_AQUI")
memoria_notas_processadas = []
# =================================================================

ssw_logado = False
aba_portal = None
aba_principal_ssw = None
tentativas_maximas_loop = 10
loop_atual = 1

# =====================================================================
# ETAPA 1: LOGIN E NAVEGAÇÃO NO PORTAL (EXECUTADO APENAS UMA VEZ)
# =====================================================================
print("Acessando o Portal Emissor...")
navegador.get("https://portal-dedicado.vercel.app/login")
aba_portal = navegador.window_handles[0]

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
# LOOP PRINCIPAL: A REPETIR A BUSCA ATÉ ACABAREM AS NOTAS
# =====================================================================
while loop_atual <= tentativas_maximas_loop:
    print(f"\n{'=' * 60}")
    print(f"🔄 INICIANDO LOOP #{loop_atual} de {tentativas_maximas_loop}")
    print(f"{'=' * 60}")

    # Volta para o portal e recarrega para atualizar o status das notas
    navegador.switch_to.window(aba_portal)
    navegador.refresh()
    time.sleep(4)

    # Reaplica Filtro de Pendentes
    try:
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

    print("Buscando notas da Automação e do tipo Carreteiro (C)...")
    try:
        linhas_tabela = espera.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody//tr")))
    except Exception:
        print("Nenhuma nota encontrada na tabela. Fim do processo.")
        break

    # Variáveis da rodada atual
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
            # === INTEGRAÇÃO DA MEMÓRIA ===
            try:
                vrid_leitura_rapida = linha.find_element(By.XPATH, ".//td[2]").text.strip()
                if any(vrid_leitura_rapida == mem_vrid for mem_vrid, _ in memoria_notas_processadas):
                    continue
            except Exception:
                pass

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

            # 3. REGRA DE DECISÃO: Pula se NÃO tiver o nome "automação"
            if "automa" not in nome_emitente.lower():
                nome_print = nome_emitente if nome_emitente != "" else "Sem nome"
                motivo_borda = " (Tinha borda vermelha, mas foi ignorada)" if tem_borda_vermelha else ""
                print(f"⏭️ Pulando linha {index + 1}: Atribuída a '{nome_print}'{motivo_borda}.")
                continue

            # 4. Verifica se o Tipo é 'C' (Carreteiro)
            span_tipo = linha.find_elements(By.XPATH, ".//span[@title='Relacionamento: CARRETEIRO' or text()='C']")

            if len(span_tipo) > 0:
                motivo = f"Nome ('{nome_emitente}') + Borda Vermelha" if (
                            tem_nome and tem_borda_vermelha) else f"Nome ('{nome_emitente}')"
                print(f"✅ Linha {index + 1} validada! (Motivo: {motivo} | Tipo: C)")

                # --- EXTRAÇÃO DE DADOS BÁSICOS ---
                try:
                    texto_origem = linha.find_element(By.XPATH, ".//td[4]").text
                    linha_origem = texto_origem.split('\n')[0]
                    if "-" in linha_origem:
                        cidade_origem = linha_origem.split('-')[0].strip()
                        estado_origem = linha_origem.split('-')[1].strip().upper()
                    elif "/" in linha_origem:
                        cidade_origem = linha_origem.split('/')[0].strip()
                        estado_origem = linha_origem.split('/')[1].strip().upper()
                    else:
                        cidade_origem = linha_origem.strip()
                        estado_origem = "MG"

                    cidade_origem = unicodedata.normalize('NFKD', cidade_origem).encode('ASCII', 'ignore').decode('utf-8')
                except Exception:
                    cidade_origem = "CONTAGEM"
                    estado_origem = "MG"

                estado_destino = ""
                try:
                    texto_destino = linha.find_element(By.XPATH, ".//td[5]").text
                    linha_destino_completa = texto_destino.split('\n')[0]

                    if " - " in linha_destino_completa:
                        cidade_destino = linha_destino_completa.split(' - ')[0].strip()
                        estado_destino = linha_destino_completa.split(' - ')[1].strip()[:2].upper()
                    else:
                        cidade_destino = linha_destino_completa.strip()

                    cidade_destino = unicodedata.normalize('NFKD', cidade_destino).encode('ASCII', 'ignore').decode('utf-8')

                    linha_data_hora = texto_destino.split('\n')[1]
                    data_bruta = linha_data_hora.split(' - ')[0].strip()
                    partes_data = data_bruta.split('/')
                    data_previsao = f"{partes_data[0]}{partes_data[1]}{partes_data[2][-2:]}"
                    hora_previsao = linha_data_hora.split(' - ')[1].strip().replace(":", "")
                except Exception:
                    cidade_destino = ""
                    data_previsao = ""
                    hora_previsao = ""

                # =================================================================
                # NOVA REGRA: EXCLUSÃO DE ROTAS DO NORDESTE
                # =================================================================
                estados_nordeste = ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]
                if estado_origem in estados_nordeste or estado_destino in estados_nordeste:
                    print(
                        f"🌵 Pulando nota {index + 1}: A rota entra ou sai do Nordeste ({estado_origem} -> {estado_destino}).")
                    continue
                # =================================================================

                vrid_extraido = linha.find_element(By.XPATH, ".//td[2]").text.strip()

                texto_linha = linha.text.upper()
                padrao_placa = re.search(r'\b[A-Z]{3}-?[0-9][A-Z0-9][0-9]{2}\b', texto_linha)
                if padrao_placa:
                    placa_extraida = padrao_placa.group(0).replace("-", "").strip()
                else:
                    try:
                        placa_extraida = linha.find_element(By.XPATH,
                                                            ".//td[contains(@class, 'font-mono')]").text.strip()
                    except:
                        placa_extraida = ""

                # Valor a Pagar
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

                # Pop-up (Emitir) para capturar PIX
                pagamento_extraido = "100%"
                pix_extraido = ""
                try:
                    botao_emitir = linha.find_element(By.XPATH,
                                                      ".//button[contains(text(), 'Emitir') or contains(@class, 'bg-emerald')]")
                    navegador.execute_script("arguments[0].click();", botao_emitir)
                    print("Aguardando pop-up do portal para extrair PIX e Pagamento...")
                    time.sleep(2)

                    try:
                        pagamento_extraido = navegador.find_element(By.XPATH,
                                                                    "//*[contains(text(), 'PAGAMENTO')]/following-sibling::*[1]").text.strip()
                    except Exception:
                        pass

                    try:
                        pix_extraido = navegador.find_element(By.XPATH,
                                                              "//*[text()='PIX' or contains(text(), 'PIX')]/following-sibling::*[1]").text.strip()
                    except Exception:
                        pass

                    if not pix_extraido:
                        try:
                            bloco_pix = navegador.find_element(By.XPATH,
                                                               "//*[text()='PIX' or contains(text(), 'PIX')]/..").text
                            pix_extraido = \
                            bloco_pix.replace("PIX", "").replace("DADOS PROPRIETÁRIO", "").strip().split("\n")[0]
                        except Exception:
                            pass

                    botao_cancelar = navegador.find_element(By.XPATH, "//button[contains(text(), 'Cancelar')]")
                    navegador.execute_script("arguments[0].click();", botao_cancelar)
                    time.sleep(1)
                except Exception as e:
                    pass

                print(
                    f"🎯 Dados: VRID {vrid_extraido} | Placa {placa_extraida} | Origem {cidade_origem}-{estado_origem} | Destino {cidade_destino} | Data {data_previsao} | Valor {valor_pagar} | Pag {pagamento_extraido} | PIX {pix_extraido}")
                nota_encontrada = True
                break

        except Exception as e:
            pass

    if not nota_encontrada:
        print("Nenhuma nota 'C' da Automação foi encontrada na página. Encerrando Robô.")
        break

    # =====================================================================
    # ETAPA 3: LOGIN NO SSW
    # =====================================================================
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
        time.sleep(3)
        ssw_logado = True
    else:
        print("SSW já logado, voltando para ele...")
        for handle in list(navegador.window_handles):
            if handle != aba_portal and handle != aba_principal_ssw:
                navegador.switch_to.window(handle)
                navegador.close()
                time.sleep(0.5)
        navegador.switch_to.window(aba_principal_ssw)
        time.sleep(1)

    # =====================================================================
    # ETAPA 4: NAVEGAR PARA TELA 72 E PREENCHER PLACA
    # =====================================================================
    print(f"Definindo a unidade do SSW com base no estado ({estado_origem})...")
    unidade_ssw = f"{str(estado_origem)[:2].upper()}E"
    print(f"✅ Unidade SSW: {unidade_ssw}")

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
    campo_opcao.send_keys("72", Keys.ENTER)

    print("A aguardar que a janela 72 abra...")
    espera.until(EC.number_of_windows_to_be(len(janelas_antes_72) + 1))
    aba_nova_72 = [j for j in navegador.window_handles if j not in janelas_antes_72][0]
    navegador.switch_to.window(aba_nova_72)
    navegador.maximize_window()
    print(f"✅ Foco alterado para a Tela 72!")

    print(f"A preencher a placa ({placa_extraida})...")
    campo_placa = WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.ID, "placa_veic")))
    navegador.execute_script("arguments[0].scrollIntoView(true);", campo_placa)
    time.sleep(0.5)
    campo_placa.clear()
    time.sleep(0.5)
    campo_placa.send_keys(placa_extraida)
    time.sleep(1)

    try:
        btn_enviar = navegador.find_element(By.ID, "btn_env")
        navegador.execute_script("arguments[0].click();", btn_enviar)
        print("✅ Botão de enviar clicado com sucesso!")
    except Exception:
        campo_placa.send_keys(Keys.ENTER)

    time.sleep(2)

    try:
        alerta_navegador = navegador.switch_to.alert
        texto_alerta = alerta_navegador.text
        alerta_navegador.accept()
        print(f"⚠️ Alerta do navegador fechado: '{texto_alerta}'")
        time.sleep(1)
    except Exception:
        pass

    # Confirmar Pop-ups Iniciais
    print("Aguardando confirmação de emissão de CTRB (1º Pop-up)...")
    try:
        xpath_ctrb = "//a[@id='0' and contains(text(), 'CTRB')]"
        botao_ctrb = WebDriverWait(navegador, 8).until(EC.visibility_of_element_located((By.XPATH, xpath_ctrb)))
        navegador.execute_script("arguments[0].click();", botao_ctrb)
        print("✅ Opção '2. Emitir novo CTRB assim mesmo.' clicada com sucesso!")
        time.sleep(4)
    except Exception:
        print("ℹ️ 1º Pop-up (CTRB) não apareceu.")

    print("Aguardando aviso de falta de Manifesto (2º Pop-up)...")
    try:
        xpath_manifesto = "//a[@id='0' and contains(text(), 'Continuar')]"
        botao_manifesto = WebDriverWait(navegador, 8).until(
            EC.visibility_of_element_located((By.XPATH, xpath_manifesto)))
        navegador.execute_script("arguments[0].click();", botao_manifesto)
        print("✅ Opção '2. Continuar assim mesmo.' (Manifesto) clicada com sucesso!")
        time.sleep(3)
    except Exception:
        print("ℹ️ 2º Pop-up (Manifesto) não apareceu.")

    print("\n✅ Fluxo inicial da Tela 72 concluído!")
    time.sleep(2)

    # =====================================================================
    # ETAPA 5: PREENCHER CEP ORIGEM (Anti-Fantasmas + Sem Acentos)
    # =====================================================================
    print("\nAguardando a tela de Terceiro carregar...")
    try:
        time.sleep(3)
        navegador.switch_to.window(navegador.window_handles[-1])
        navegador.maximize_window()

        # 1. Clica no link 'CEP origem'
        xpath_link_cep = "//*[@id='link_cep_orig' or contains(text(), 'CEP')]"
        link_cep_origem = WebDriverWait(navegador, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath_link_cep))
        )
        navegador.execute_script("arguments[0].click();", link_cep_origem)
        print("✅ Link 'CEP origem' clicado!")

        print("Aguardando a caixa de pesquisa da cidade abrir...")
        time.sleep(2)

        # 2. O SEGREDO: Procura a caixa APENAS dentro do painel que está VISÍVEL!
        xpath_caixa_verdadeira = "//div[@id='errormsg' and contains(@style, 'visible')]//input[@id='-1']"
        campo_busca = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_caixa_verdadeira))
        )

        # 3. TRATAMENTO DE ACENTOS (Ex: 'RIBEIRÃO' -> 'RIBEIRAO')
        import unicodedata

        cidade_limpa = unicodedata.normalize('NFKD', cidade_origem).encode('ASCII', 'ignore').decode('utf-8')

        # 4. Escreve a cidade e dá ENTER
        campo_busca.clear()
        time.sleep(0.5)
        campo_busca.send_keys(cidade_limpa)
        time.sleep(1)
        campo_busca.send_keys(Keys.ENTER)

        print("Verificando se a lista azul de cidades vai aparecer...")

        # 5. TRATAMENTO INTELIGENTE: Pode não haver lista se o SSW aceitar o nome exato!
        try:
            primeira_palavra = cidade_limpa.lower().split()[0]
            xpath_cidade_lista = f"//tr//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{primeira_palavra}')]"

            # Espera no máximo 4 segundos. Se não aparecer, avança!
            link_cidade_resultado = WebDriverWait(navegador, 4).until(
                EC.element_to_be_clickable((By.XPATH, xpath_cidade_lista))
            )
            navegador.execute_script("arguments[0].click();", link_cidade_resultado)
            print(f"✅ Cidade de Origem '{cidade_limpa}' selecionada na lista com sucesso!")
        except Exception:
            print(
                f"ℹ️ O SSW encontrou correspondência exata e aceitou '{cidade_limpa}' automaticamente (sem lista azul).")

    except Exception as e:
        print(f"⚠️ Erro ao tentar preencher o CEP de origem: {e}")

    # 6. PAUSA VITAL: Espera o pop-up fechar antes de ir para o destino
    time.sleep(4)
    navegador.switch_to.window(navegador.window_handles[-1])

    # =====================================================================
    # ETAPA 6: PREENCHER UNIDADE DE DESTINO (FEC)
    # =====================================================================
    print("\nPreenchendo Unidade de Destino (FEC)...")
    try:
        campo_unidade_dest = WebDriverWait(navegador, 20).until(
            EC.element_to_be_clickable((By.ID, "id_filial_sigla_dest"))
        )
        navegador.execute_script("arguments[0].click();", campo_unidade_dest)
        time.sleep(0.5)
        campo_unidade_dest.send_keys(Keys.CONTROL, "a")
        campo_unidade_dest.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)

        # Escreve FEC e dá TAB
        campo_unidade_dest.send_keys("FEC", Keys.TAB)
        time.sleep(2)
        print("✅ Unidade destino 'FEC' preenchida!")
    except Exception as e:
        print(f"⚠️ Erro ao preencher destino 'FEC': {e}")

    # TRATAMENTO DO POP-UP "7. OK" (Caso a unidade FEC ative alerta)
    print("Aguardando possível pop-up '7. OK' da unidade de destino...")
    try:
        xpath_7ok = "//a[contains(text(), '7. OK') or contains(text(), '7.')]"
        botao_7ok = WebDriverWait(navegador, 4).until(
            EC.visibility_of_element_located((By.XPATH, xpath_7ok))
        )
        navegador.execute_script("arguments[0].click();", botao_7ok)
        print("✅ Pop-up '7. OK' fechado com sucesso!")
        time.sleep(2)
    except Exception:
        print("ℹ️ Pop-up '7. OK' não apareceu.")


        # =====================================================================
        # ETAPA 7: PREENCHER CEP DESTINO E PREVISÃO (Anti-Fantasmas + Sem Acentos)
        # =====================================================================
        print("\nIniciando o preenchimento do CEP de destino...")
        try:
            time.sleep(2)
            xpath_link_cep_dest = "//*[@id='link_cep_dest']"
            link_cep_destino = WebDriverWait(navegador, 15).until(
                EC.element_to_be_clickable((By.XPATH, xpath_link_cep_dest))
            )
            navegador.execute_script("arguments[0].click();", link_cep_destino)
            print("✅ Link 'CEP destino' clicado!")

            print("Aguardando a caixa de pesquisa da cidade (destino) abrir...")
            time.sleep(2)

            # Procura a caixa APENAS dentro do painel que está VISÍVEL!
            xpath_caixa_verdadeira_dest = "//div[@id='errormsg' and contains(@style, 'visible')]//input[@id='-1']"
            campo_busca_dest = WebDriverWait(navegador, 15).until(
                EC.element_to_be_clickable((By.XPATH, xpath_caixa_verdadeira_dest))
            )

            janelas_antes_cidade = navegador.window_handles

            # TRATAMENTO DE ACENTOS
            import unicodedata

            cidade_destino_limpa = unicodedata.normalize('NFKD', cidade_destino).encode('ASCII', 'ignore').decode(
                'utf-8')

            # Escreve a cidade e dá ENTER
            campo_busca_dest.clear()
            time.sleep(0.5)
            campo_busca_dest.send_keys(cidade_destino_limpa)
            time.sleep(1)
            campo_busca_dest.send_keys(Keys.ENTER)

            print("Verificando se a lista azul de cidades (Destino) vai aparecer...")

            # TRATAMENTO INTELIGENTE DA LISTA AZUL (Mesma lógica da origem)
            try:
                primeira_palavra_dest = cidade_destino_limpa.lower().split()[0]
                xpath_cidade_lista_dest = f"//tr//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{primeira_palavra_dest}')]"

                link_cidade_resultado_dest = WebDriverWait(navegador, 4).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_cidade_lista_dest))
                )
                navegador.execute_script("arguments[0].click();", link_cidade_resultado_dest)
                print(f"✅ Cidade de Destino '{cidade_destino_limpa}' selecionada na lista com sucesso!")
            except Exception:
                print(
                    f"ℹ️ O SSW encontrou correspondência exata e aceitou '{cidade_destino_limpa}' automaticamente (sem lista azul).")

            # INTELIGÊNCIA: Verificando a tela 027 (Cadastro)
            print("Verificando se o SSW forçou a abertura da tela '027 - Cadastro'...")
            time.sleep(4)
            janelas_depois_cidade = navegador.window_handles
            if len(janelas_depois_cidade) > len(janelas_antes_cidade):
                aba_027 = [j for j in janelas_depois_cidade if j not in janelas_antes_cidade][0]
                navegador.switch_to.window(aba_027)
                navegador.maximize_window()
                print("⚠️ Ecrã 027 detetado! A fechar a pendência...")

                botao_mais = WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.ID, "btn_mais")))
                navegador.execute_script("arguments[0].click();", botao_mais)
                print("✅ Botão de gravação (seta azul) clicado no ecrã 027!")
                time.sleep(3)
            else:
                print("ℹ️ Nenhuma pendência detetada. O fluxo continua.")

        except Exception as e:
            print(f"⚠️ Erro ao tentar preencher o CEP de destino: {e}")

        time.sleep(4)
        navegador.switch_to.window(navegador.window_handles[-1])



    # Preenchendo a Previsão de Chegada (Data e Hora)
    print("\nPreenchendo a Previsão de Chegada (Data e Hora)...")
    formato_data = "%d%m%y"
    if data_previsao and hora_previsao:
        try:
            data_obj = datetime.strptime(str(data_previsao).strip(), formato_data).date()
            hoje = datetime.now().date()
            if data_obj <= hoje:
                data_previsao = (hoje + timedelta(days=1)).strftime(formato_data)
                print(f"⚠️ Data ajustada para amanhã: {data_previsao}")
            else:
                print(f"Data de previsão {data_previsao} é futura. Mantendo a data original. ")
        except ValueError:
            pass

        try:
            campo_data = WebDriverWait(navegador, 5).until(EC.presence_of_element_located((By.ID, "id_data_prev_cheg")))
            navegador.execute_script("arguments[0].focus();", campo_data)
            time.sleep(0.5)
            campo_data.clear()
            campo_data.send_keys(data_previsao, Keys.TAB)
            time.sleep(3)

            print("Aguardando possível pop-up '7. OK' da Data...")
            try:
                xpath_7ok_data = "//a[contains(text(), '7. OK') or contains(text(), '7.')]"
                botao_7ok_data = WebDriverWait(navegador, 3).until(
                    EC.visibility_of_element_located((By.XPATH, xpath_7ok_data)))
                navegador.execute_script("arguments[0].click();", botao_7ok_data)
                print("✅ Pop-up '7. OK' (Data) fechado!")
                time.sleep(2)
            except Exception:
                print("ℹ Pop-up de Data não apareceu.")
        except Exception:
            print("ℹ️ Campo de DATA não encontrado.")

        try:
            campo_hora = navegador.find_element(By.ID, "id_hora_prev_cheg")
            navegador.execute_script("arguments[0].focus();", campo_hora)
            time.sleep(0.5)
            campo_hora.clear()
            campo_hora.send_keys(hora_previsao)
        except Exception:
            print("ℹ️ Campo de HORA não encontrado.")

        print(f"✅ Previsão de chegada preenchida com sucesso!")

    # =====================================================================
    # ETAPA 8: PREENCHER DADOS FINAIS E EMITIR
    # =====================================================================
    print("\nPreenchendo Natureza, Valor e Observações...")
    try:
        try:
            WebDriverWait(navegador, 15).until(EC.invisibility_of_element_located((By.ID, "procimg")))
        except Exception:
            pass

        campo_nat_carga = navegador.find_element(By.ID, "id_nat_carga")
        navegador.execute_script("arguments[0].focus();", campo_nat_carga)
        time.sleep(0.5)
        campo_nat_carga.clear()
        campo_nat_carga.send_keys("1", Keys.TAB)
        time.sleep(0.5)

        campo_valor = navegador.find_element(By.ID, "id_vlr_ficha")
        navegador.execute_script("arguments[0].focus();", campo_valor)
        time.sleep(0.5)
        campo_valor.clear()
        campo_valor.send_keys(valor_pagar)

        campo_obs1 = navegador.find_element(By.ID, "id_obs1")
        campo_obs1.send_keys(f"PAGAMENTO: {pagamento_extraido}")

        campo_obs2 = navegador.find_element(By.ID, "id_obs2")
        campo_obs2.send_keys(f"ID: {vrid_extraido} - Placa: {placa_extraida} ")
        time.sleep(0.5)

        campo_obs3 = navegador.find_element(By.ID, "id_obs3")
        campo_obs3.send_keys(f"PIX: {pix_extraido}")

        print("✅ Todos os dados preenchidos com sucesso!")

    except Exception as e:
        print(f"⚠️ Erro ao preencher os dados finais: {e}")

    time.sleep(3)

    # --------------------------------------------------
    # ETAPA FINAL: CLICAR NA SETINHA DE ENVIAR
    # --------------------------------------------------
    sucesso_emissao = False
    try:
        print("Realizando scroll até o botão final de emissão...")
        botao_enviar_final = WebDriverWait(navegador, 5).until(
            EC.presence_of_element_located((By.ID, "id_link_env"))
        )
        navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_enviar_final)
        time.sleep(1)

        print("Acionando a função interna de envio do SSW...")
        navegador.execute_script("f_button_env_disable(); ajaxEnvia('CTRB_RPA', 0);")
        print("🚀 COMANDO DE EMISSÃO ENVIADO.")
    except Exception as e:
        print(f"⚠️ Erro na etapa final de emissão: {e}")

    time.sleep(13)

    # --------------------------------------------------
    # CLICANDO NO POP 1. Continuar E SALVANDO NA MEMÓRIA
    # --------------------------------------------------
    print("Aguardando pop-up de sucesso '1. Continuar'...")
    try:
        xpath_1continuar = "//*[@id='-4' and contains(@class, 'dialog')]"
        botao_continuar = WebDriverWait(navegador, timeout=8).until(
            EC.presence_of_element_located((By.XPATH, xpath_1continuar))
        )
        navegador.execute_script("arguments[0].click();", botao_continuar)
        print("✅ Pop-up '1. Continuar' clicado e fechado com sucesso!")
        sucesso_emissao = True
        time.sleep(3)
    except Exception:
        print("ℹ️ Pop-up '1. Continuar' não apareceu. Assumindo sucesso pelo clique do envio.")
        sucesso_emissao = True

    # === INTELIGÊNCIA: GRAVANDO O RESULTADO NA MEMÓRIA ===
    if sucesso_emissao:
        memoria_notas_processadas.append((vrid_extraido, placa_extraida))
        print(
            f"💾 Memória Atualizada! O robô gravou o VRID [{vrid_extraido}] e a Placa [{placa_extraida}] para não repeti-los na próxima volta.")
    # =====================================================

        # =====================================================================
        # FLUXO 4: ANEXAR CTRB E CONFIRMAR EMISSÃO NO PORTAL
        # =====================================================================
        print("\n--- ANEXANDO CTRB E CONFIRMANDO NO PORTAL ---")
        caminho_arquivo_ctrb = r"C:\Users\Transking\OneDrive\Área de Trabalho\Emissor_Doc_Fiscal.pdf"

        try:
            xpath_input_ctrb = "//span[contains(text(), 'CTRB')]/following-sibling::input[@type='file']"
            input_ctrb = espera.until(EC.presence_of_element_located((By.XPATH, xpath_input_ctrb)))
            input_ctrb.send_keys(caminho_arquivo_ctrb)
            print("✅ Arquivo CTRB anexado com sucesso!")
            time.sleep(6)
        except Exception as e:
            print(f"⚠️ Erro ao anexar o CTRB: {e}")

        try:
            botao_confirmar = navegador.find_element(By.XPATH,
                                                     "//button[contains(text(), 'Confirmar Emissão') or contains(text(), 'OK')]")
            navegador.execute_script("arguments[0].click();", botao_confirmar)
            print("✅ Emissão CONFIRMADA E FINALIZADA no portal Amazon!")
            time.sleep(3)
        except Exception as e:
            print("⚠️ Botão de confirmação não encontrado. Tentando fechar no Cancelar/X...")
            try:
                botao_fechar_nota_portal = navegador.find_element(By.XPATH,
                                                                  "//button[contains(text(), 'Cancelar') or contains(@class, 'lucide-x')]")
                navegador.execute_script("arguments[0].click();", botao_fechar_nota_portal)
            except:
                pass

        print("✅ De volta ao portal! Buscando próxima nota...")

    print(f"\n✅ Fluxo da Volta {loop_atual} concluído! Preparando próxima volta...")
    loop_atual += 1

# --- FIM DO WHILE ---
print("\n🤖 Automação finalizada com sucesso! O robô cumpriu o seu propósito.")
navegador.quit()