import json
from datetime import datetime, date

ARQUIVO_DB = 'clinica.json'
LISTAS_DB = ("tutores", "animais", "procedimentos")

TIPOS_PROCEDIMENTO = {
    1: ("Vacinação", "nome da vacina"),
    2: ("Castração", None),
    3: ("Exame", "nome do exame"),
    4: ("Consulta", None),
    5: ("Cirurgia", "nome da cirurgia"),
}

# ----------------------------------------------------------------------------
# Funções de apoio
# ----------------------------------------------------------------------------
def proximo_id(lista):
    if not lista:
        return 1
    return max(item["id"] for item in lista) + 1


def buscar_id(lista, id_busca):
    for item in lista:
        if item["id"] == id_busca:
            return item
    return None


def carregar_db():
    try:
        with open(ARQUIVO_DB, 'r', encoding='utf-8') as arquivo:
            clinica = json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        clinica = {}
    for chave in LISTAS_DB:
        clinica.setdefault(chave, [])
    return clinica


def salvar_db(clinica):
    with open(ARQUIVO_DB, 'w', encoding='utf-8') as arquivo:
        json.dump(clinica, arquivo, ensure_ascii=False, indent=4)


def formatar_data(data_iso):
    """Converte a data guardada (aaaa-mm-dd) para exibição (dd/mm/aaaa)."""
    try:
        return date.fromisoformat(data_iso).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return "N/A"


def ler_int(mensagem):
    """Lê um número inteiro. Devolve None se o usuário digitar algo inválido."""
    try:
        return int(input(mensagem).strip())
    except ValueError:
        print('Digite apenas números.')
        return None


def ler_texto(mensagem):
    """Lê um texto que não pode ficar vazio."""
    while True:
        texto = input(mensagem).strip()
        if texto:
            return texto
        print('Este campo não pode ficar vazio.')


def ler_telefone(mensagem):
    while True:
        telefone = input(mensagem).strip()
        if telefone.isdigit():
            return telefone
        print('Digite apenas números, sem parênteses ou hífen.')


def ler_peso(mensagem):
    while True:
        try:
            peso = float(input(mensagem).replace(",", "."))
        except ValueError:
            print('Digite um valor numérico (ex.: 12,5).')
            continue
        if 0 < peso < 500:
            return peso
        print('O peso deve ser maior que 0 e menor que 500 kg.')


def ler_data(mensagem):
    """Lê uma data futura no formato dd/mm/aaaa. Devolve None se inválida."""
    texto = input(mensagem).strip()
    try:
        data_lida = datetime.strptime(texto, '%d/%m/%Y').date()
    except ValueError:
        print('Formato de data incorreto. Use dd/mm/aaaa.')
        return None
    if data_lida < date.today():
        print('A data não pode ser anterior ao dia atual.')
        return None
    return data_lida


def pausar():
    input('\nAperte Enter para voltar ao menu...')


# ----------------------------------------------------------------------------
# Funções de consulta e exibição
# ----------------------------------------------------------------------------
def nome_do_tutor(clinica, animal):
    """Nome do tutor de um animal, tolerando vínculo quebrado."""
    if animal is None:
        return "-"
    tutor = buscar_id(clinica["tutores"], animal["id_tutor"])
    return tutor["nome"] if tutor else "(tutor removido)"


def listar_tutores(clinica):
    """Imprime os tutores. Devolve False se não houver nenhum."""
    if not clinica["tutores"]:
        print('Nenhum tutor cadastrado.')
        return False
    for tutor in clinica["tutores"]:
        print('ID: {} | NOME: {} | TELEFONE: {} | E-MAIL: {}'.format(
            tutor["id"], tutor["nome"], tutor["telefone"], tutor["email"]))
    return True


def listar_animais(clinica):
    """Imprime os animais. Devolve False se não houver nenhum."""
    if not clinica["animais"]:
        print('Nenhum animal cadastrado.')
        return False
    for animal in clinica["animais"]:
        print('ID: {} | NOME: {} | ESPÉCIE: {} | TUTOR: {}'.format(
            animal["id"], animal["nome"], animal.get("especie", "N/A"),
            nome_do_tutor(clinica, animal)))
    return True


def selecionar_animal(clinica):
    """Lista os animais e devolve o escolhido, ou None."""
    if not listar_animais(clinica):
        return None
    print("-" * 50)
    id_animal = ler_int('ID do animal: ')
    if id_animal is None:
        return None
    animal = buscar_id(clinica["animais"], id_animal)
    if animal is None:
        print('Nenhum animal encontrado com esse ID.')
    return animal


def procedimentos_do_animal(clinica, id_animal, tipo=None):
    """Procedimentos de um animal, opcionalmente filtrados por tipo, em ordem de data."""
    encontrados = []
    for procedimento in clinica["procedimentos"]:
        if procedimento["id_animal"] != id_animal:
            continue
        if tipo is not None and procedimento["tipo"] != tipo:
            continue
        encontrados.append(procedimento)
    encontrados.sort(key=lambda item: item.get("data", ""))
    return encontrados


def contar_vinculos(clinica, tutor):
    """Quantos animais e procedimentos seriam apagados junto com este tutor."""
    ids_animais = []
    for animal in clinica["animais"]:
        if animal["id_tutor"] == tutor["id"]:
            ids_animais.append(animal["id"])

    total_procedimentos = 0
    for procedimento in clinica["procedimentos"]:
        if procedimento["id_animal"] in ids_animais:
            total_procedimentos += 1

    return ids_animais, total_procedimentos


def excluir_tutor_em_cascata(clinica, tutor):
    """Remove o tutor, seus animais e os procedimentos desses animais."""
    ids_animais, _ = contar_vinculos(clinica, tutor)

    procedimentos_restantes = []
    for procedimento in clinica["procedimentos"]:
        if procedimento["id_animal"] not in ids_animais:
            procedimentos_restantes.append(procedimento)

    animais_restantes = []
    for animal in clinica["animais"]:
        if animal["id_tutor"] != tutor["id"]:
            animais_restantes.append(animal)

    clinica["procedimentos"] = procedimentos_restantes
    clinica["animais"] = animais_restantes
    clinica["tutores"].remove(tutor)


def cabecalho(titulo):
    print("=" * 50)
    print("🐾  VetSys{}".format(titulo).center(50))
    print("=" * 50)
    print("Bem-vindo ao sistema VetSys!".center(50))
    print("Um sistema desenvolvido para clínicas veterinárias.".center(50))
    print("-" * 50)


clinica = carregar_db()

# ----------------------------------------------------------------------------
# Menu principal
# ----------------------------------------------------------------------------
while True:
    cabecalho("")
    print("  [1] Cadastro de animais e tutores")
    print("  [2] Agendamento de procedimentos")
    print("  [3] Carteira de vacinação")
    print("  [4] Histórico e ficha do animal")
    print("  [5] Sair")
    print("=" * 50)

    input_usuario = ler_int('Digite a opção desejada: ')
    if input_usuario is None:
        continue

    # ------------------------------------------------------------------------
    # 1 - Cadastro de animais e tutores
    # ------------------------------------------------------------------------
    if input_usuario == 1:
        while True:
            cabecalho(" - Cadastro de animais e tutores")
            print("  [1] Cadastrar tutor")
            print("  [2] Cadastrar animal")
            print("  [3] Visualizar tutores e animais")
            print("  [4] Editar ou excluir tutores")
            print("  [5] Voltar")
            print("=" * 50)

            input_cadastro = ler_int('Digite a opção desejada: ')
            if input_cadastro is None:
                continue

            if input_cadastro == 1:
                print("Cadastro de tutor selecionado.")
                nome_tutor = ler_texto("Digite o nome do tutor: ")
                telefone_tutor = ler_telefone("Digite o telefone do tutor (apenas números): ")
                email_tutor = ler_texto("Digite o e-mail do tutor: ")

                tutor = {
                    "id": proximo_id(clinica["tutores"]),
                    "nome": nome_tutor,
                    "telefone": telefone_tutor,
                    "email": email_tutor,
                }
                clinica["tutores"].append(tutor)
                salvar_db(clinica)
                print("Tutor {} cadastrado com sucesso! (ID {})".format(nome_tutor, tutor["id"]))
                pausar()

            elif input_cadastro == 2:
                print("Cadastro de animal selecionado.")
                print("=" * 50)
                print("Selecione o ID de um tutor para vincular ao animal.".center(50))
                print("-" * 50)

                if not listar_tutores(clinica):
                    print('Cadastre um tutor antes de cadastrar um animal.')
                    pausar()
                    continue

                print("-" * 50)
                id_tutor = ler_int('ID do tutor: ')
                if id_tutor is None:
                    pausar()
                    continue

                tutor_selecionado = buscar_id(clinica["tutores"], id_tutor)
                if tutor_selecionado is None:
                    print('Nenhum tutor encontrado com esse ID.')
                    pausar()
                    continue

                nome_animal = ler_texto('Digite o nome do animal: ')
                especie_animal = ler_texto('Digite a espécie do animal: ')
                raca_animal = ler_texto('Digite a raça do animal: ')
                sexo_animal = ler_texto('Digite o sexo do animal: ')
                idade_animal = ler_texto('Digite a idade do animal: ')
                peso_animal = ler_peso('Digite o peso do animal (kg): ')

                animal = {
                    "id": proximo_id(clinica["animais"]),
                    "id_tutor": tutor_selecionado["id"],
                    "nome": nome_animal,
                    "especie": especie_animal,
                    "raca": raca_animal,
                    "sexo": sexo_animal,
                    "idade": idade_animal,
                    "peso": peso_animal,
                }
                clinica["animais"].append(animal)
                salvar_db(clinica)
                print("Animal {} cadastrado com sucesso! (ID {})".format(nome_animal, animal["id"]))
                pausar()

            elif input_cadastro == 3:
                print("=" * 50)
                print("Visualização dos cadastros.".center(50))
                print("-" * 50)

                if not clinica["tutores"]:
                    print('Nenhum tutor cadastrado.')
                else:
                    for tutor in clinica["tutores"]:
                        print('Tutor  - ID: {} | NOME: {} | TELEFONE: {} | E-MAIL: {}'.format(
                            tutor["id"], tutor["nome"], tutor["telefone"], tutor["email"]))

                        encontrados = 0
                        for animal in clinica["animais"]:
                            if animal["id_tutor"] == tutor["id"]:
                                encontrados += 1
                                print('  Animal - ID: {} | NOME: {} | ESPÉCIE: {} | RAÇA: {} | '
                                      'SEXO: {} | IDADE: {} | PESO: {} kg'.format(
                                          animal["id"], animal["nome"],
                                          animal.get("especie", "N/A"), animal.get("raca", "N/A"),
                                          animal.get("sexo", "N/A"), animal.get("idade", "N/A"),
                                          animal.get("peso", "N/A")))
                        if encontrados == 0:
                            print('  Nenhum animal cadastrado para este tutor.')
                        print("-" * 50)
                pausar()

            elif input_cadastro == 4:
                print("=" * 50)
                print("Selecione o ID de um tutor para editar ou excluir.".center(50))
                print("-" * 50)

                if not listar_tutores(clinica):
                    pausar()
                    continue

                print("-" * 50)
                input_id = ler_int('ID do tutor: ')
                if input_id is None:
                    pausar()
                    continue

                tutor_selecionado = buscar_id(clinica["tutores"], input_id)
                if tutor_selecionado is None:
                    print('Nenhuma ficha encontrada com esse ID.')
                    pausar()
                    continue

                print("-" * 50)
                print("  [1] Editar tutor")
                print("  [2] Excluir tutor")
                print("  [3] Voltar")
                print("-" * 50)

                input_opcao = ler_int('Selecione a opção desejada: ')
                if input_opcao is None or input_opcao == 3:
                    continue

                if input_opcao == 1:
                    novo_nome = ler_texto('Digite o novo nome: ')
                    novo_telefone = ler_telefone('Digite o novo telefone (apenas números): ')
                    novo_email = ler_texto('Digite o novo e-mail: ')

                    tutor_selecionado["nome"] = novo_nome
                    tutor_selecionado["telefone"] = novo_telefone
                    tutor_selecionado["email"] = novo_email
                    salvar_db(clinica)

                    print("-=-" * 16)
                    print("Novo nome: {}".format(novo_nome))
                    print("Novo telefone: {}".format(novo_telefone))
                    print("Novo e-mail: {}".format(novo_email))
                    print("-=-" * 16)
                    print('Tutor editado com sucesso!')

                elif input_opcao == 2:
                    ids_animais, total_procedimentos = contar_vinculos(clinica, tutor_selecionado)
                    if ids_animais:
                        print('ATENÇÃO: este tutor possui {} animal(is) e {} procedimento(s) '
                              'vinculados, que também serão excluídos.'.format(
                                  len(ids_animais), total_procedimentos))

                    confirma_exclusao = input('Tem certeza de que quer excluir? [S/N]: ').strip().lower()
                    if confirma_exclusao == "s":
                        excluir_tutor_em_cascata(clinica, tutor_selecionado)
                        salvar_db(clinica)
                        print('Tutor excluído com sucesso!')
                    else:
                        print('Exclusão cancelada!')

                else:
                    print('Selecione uma opção correta.')

                pausar()

            elif input_cadastro == 5:
                break

            else:
                print('Opção incorreta.')

    # ------------------------------------------------------------------------
    # 2 - Agendamento de procedimentos
    # ------------------------------------------------------------------------
    elif input_usuario == 2:
        while True:
            cabecalho(" - Agendamento de procedimentos")
            print("  [1] Agendar procedimento")
            print("  [2] Editar procedimento agendado")
            print("  [3] Voltar")
            print("=" * 50)

            input_agendamento = ler_int('Digite a opção desejada: ')
            if input_agendamento is None:
                continue

            if input_agendamento == 1:
                print('Agendamento de procedimento selecionado.')
                print("=" * 50)

                animal_selecionado = selecionar_animal(clinica)
                if animal_selecionado is None:
                    pausar()
                    continue

                print("-" * 50)
                print("Selecione o tipo de procedimento".center(50))
                print("-" * 50)
                print("  [1] Vacinação")
                print("  [2] Castração")
                print("  [3] Exame")
                print("  [4] Consulta")
                print("  [5] Cirurgia")
                print("  [6] Voltar")
                print("=" * 50)

                input_procedimento = ler_int('Digite a opção desejada: ')
                if input_procedimento is None or input_procedimento == 6:
                    continue
                if input_procedimento not in TIPOS_PROCEDIMENTO:
                    print('Opção incorreta.')
                    pausar()
                    continue

                tipo, rotulo_nome = TIPOS_PROCEDIMENTO[input_procedimento]
                print('Agendamento de {} selecionado.'.format(tipo.lower()))

                nome_procedimento = None
                if rotulo_nome is not None:
                    nome_procedimento = ler_texto('Digite o {}: '.format(rotulo_nome))

                data_procedimento = ler_data('Digite a data do procedimento (dd/mm/aaaa): ')
                if data_procedimento is None:
                    pausar()
                    continue

                procedimento = {
                    "id": proximo_id(clinica["procedimentos"]),
                    "id_animal": animal_selecionado["id"],
                    "tipo": tipo,
                    "data": data_procedimento.isoformat(),
                }
                if nome_procedimento is not None:
                    procedimento["nome"] = nome_procedimento

                clinica["procedimentos"].append(procedimento)
                salvar_db(clinica)
                print('Procedimento agendado com sucesso para {} em {}.'.format(
                    animal_selecionado["nome"], formatar_data(procedimento["data"])))
                pausar()

            elif input_agendamento == 2:
                print('Edição de procedimento agendado selecionada.')
                print("=" * 50)

                if not clinica["procedimentos"]:
                    print('Nenhum procedimento agendado.')
                    pausar()
                    continue

                for procedimento in clinica["procedimentos"]:
                    animal = buscar_id(clinica["animais"], procedimento["id_animal"])
                    print('ID: {} | ANIMAL: {} | TUTOR: {} | TIPO: {} | NOME: {} | DATA: {}'.format(
                        procedimento["id"],
                        animal["nome"] if animal else "(animal removido)",
                        nome_do_tutor(clinica, animal),
                        procedimento["tipo"],
                        procedimento.get("nome", "-"),
                        formatar_data(procedimento.get("data"))))
                print("=" * 50)

                input_id_procedimento = ler_int('Digite o ID do procedimento que deseja editar: ')
                if input_id_procedimento is None:
                    pausar()
                    continue

                procedimento_selecionado = buscar_id(clinica["procedimentos"], input_id_procedimento)
                if procedimento_selecionado is None:
                    print('Nenhum procedimento encontrado com esse ID.')
                    pausar()
                    continue

                novo_nome = None
                if "nome" in procedimento_selecionado:
                    novo_nome = ler_texto('Digite o novo nome do procedimento: ')

                nova_data = ler_data('Digite a nova data do procedimento (dd/mm/aaaa): ')
                if nova_data is None:
                    print('Nada foi alterado.')
                    pausar()
                    continue

                if novo_nome is not None:
                    procedimento_selecionado["nome"] = novo_nome
                procedimento_selecionado["data"] = nova_data.isoformat()
                salvar_db(clinica)
                print('Procedimento editado com sucesso.')
                pausar()

            elif input_agendamento == 3:
                break

            else:
                print('Opção incorreta.')

    # ------------------------------------------------------------------------
    # 3 - Carteira de vacinação
    # ------------------------------------------------------------------------
    elif input_usuario == 3:
        while True:
            cabecalho(" - Carteira de vacinação")
            print("  [1] Consultar carteira de vacinação")
            print("  [2] Voltar")
            print("=" * 50)

            input_vacinacao = ler_int('Digite a opção desejada: ')
            if input_vacinacao is None:
                continue

            if input_vacinacao == 1:
                print("=" * 50)
                print("Consulta da carteira de vacinação.".center(50))
                print("-" * 50)

                animal_selecionado = selecionar_animal(clinica)
                if animal_selecionado is None:
                    pausar()
                    continue

                vacinas = procedimentos_do_animal(clinica, animal_selecionado["id"], "Vacinação")
                print("-" * 50)
                print('CARTEIRA DE {} (tutor: {})'.format(
                    animal_selecionado["nome"].upper(), nome_do_tutor(clinica, animal_selecionado)))
                print("-" * 50)

                if not vacinas:
                    print('Nenhuma vacina registrada para este animal.')
                else:
                    for vacina in vacinas:
                        print('VACINA: {} | DATA: {}'.format(
                            vacina.get("nome", "N/A"), formatar_data(vacina.get("data"))))
                pausar()

            elif input_vacinacao == 2:
                break

            else:
                print('Opção incorreta.')

    # ------------------------------------------------------------------------
    # 4 - Histórico e ficha do animal
    # ------------------------------------------------------------------------
    elif input_usuario == 4:
        while True:
            cabecalho(" - Histórico e ficha do animal")
            print("  [1] Consultar histórico do animal")
            print("  [2] Consultar ficha do animal")
            print("  [3] Voltar")
            print("=" * 50)

            input_historico = ler_int('Digite a opção desejada: ')
            if input_historico is None:
                continue

            if input_historico == 1:
                print("=" * 50)
                print("Consulta do histórico do animal.".center(50))
                print("-" * 50)

                animal_selecionado = selecionar_animal(clinica)
                if animal_selecionado is None:
                    pausar()
                    continue

                historico = procedimentos_do_animal(clinica, animal_selecionado["id"])
                print("-" * 50)
                print('HISTÓRICO DE {} (tutor: {})'.format(
                    animal_selecionado["nome"].upper(), nome_do_tutor(clinica, animal_selecionado)))
                print("-" * 50)

                if not historico:
                    print('Nenhum procedimento registrado para este animal.')
                else:
                    for procedimento in historico:
                        print('DATA: {} | TIPO: {} | NOME: {}'.format(
                            formatar_data(procedimento.get("data")),
                            procedimento.get("tipo", "N/A"),
                            procedimento.get("nome", "-")))
                pausar()

            elif input_historico == 2:
                print("=" * 50)
                print("Consulta da ficha do animal.".center(50))
                print("-" * 50)

                animal_selecionado = selecionar_animal(clinica)
                if animal_selecionado is None:
                    pausar()
                    continue

                print("-" * 50)
                print('FICHA DE {}'.format(animal_selecionado["nome"].upper()))
                print("-" * 50)
                print('TUTOR...: {}'.format(nome_do_tutor(clinica, animal_selecionado)))
                print('ESPÉCIE.: {}'.format(animal_selecionado.get("especie", "N/A")))
                print('RAÇA....: {}'.format(animal_selecionado.get("raca", "N/A")))
                print('SEXO....: {}'.format(animal_selecionado.get("sexo", "N/A")))
                print('IDADE...: {}'.format(animal_selecionado.get("idade", "N/A")))
                print('PESO....: {} kg'.format(animal_selecionado.get("peso", "N/A")))
                print('PROCEDIMENTOS: {}'.format(
                    len(procedimentos_do_animal(clinica, animal_selecionado["id"]))))
                pausar()

            elif input_historico == 3:
                break

            else:
                print('Opção incorreta.')

    # ------------------------------------------------------------------------
    elif input_usuario == 5:
        print("Saindo do sistema VetSys...")
        break

    else:
        print('Opção incorreta.')
