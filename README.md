# 🐾 VetSys — Sistema de Gestão para Clínicas Veterinárias

Sistema de linha de comando escrito em **Python puro**, sem bibliotecas externas, para gerenciar o dia a dia de uma clínica veterinária: cadastro de tutores e seus animais, agendamento de procedimentos, carteira de vacinação e histórico clínico.

O projeto nasceu como um exercício prático para aplicar, em algo com cara de sistema real, os fundamentos da linguagem que venho estudando por conta própria — e acabou virando um estudo de **modelagem de dados relacionais** sem banco de dados, usando apenas listas e dicionários.

---

## ✨ Funcionalidades

### Cadastro de tutores e animais
- **Cadastrar tutor** — nome, telefone e e-mail, com ID gerado automaticamente.
- **Cadastrar animal** — vinculado a um tutor existente, com espécie, raça, sexo, idade e peso.
- **Visualizar cadastros** — lista cada tutor com os animais vinculados a ele, indentados abaixo.
- **Editar tutor** — atualiza nome, telefone e e-mail.
- **Excluir tutor** — remove o tutor, seus animais e todos os procedimentos desses animais, avisando antes quantos registros serão afetados.

### Agendamento de procedimentos
- Cinco tipos disponíveis: **Vacinação, Castração, Exame, Consulta e Cirurgia**.
- Vacinação, Exame e Cirurgia pedem uma descrição (nome da vacina, do exame, da cirurgia); Castração e Consulta não.
- Validação de data: formato, existência real do dia e impedimento de agendar no passado.
- **Edição** de procedimentos já agendados.

### Consultas
- **Carteira de vacinação** — todas as vacinas de um animal, em ordem cronológica.
- **Histórico** — todos os procedimentos de um animal, de qualquer tipo, em ordem cronológica.
- **Ficha** — dados cadastrais do animal, o tutor responsável e o total de procedimentos.

### Persistência
- Tudo é salvo automaticamente em `clinica.json` a cada alteração.
- Os dados são recarregados ao iniciar o programa.

---

## 🎬 Exemplo de uso

```
==================================================
                    🐾  VetSys
==================================================
           Bem-vindo ao sistema VetSys!
Um sistema desenvolvido para clínicas veterinárias.
--------------------------------------------------
  [1] Cadastro de animais e tutores
  [2] Agendamento de procedimentos
  [3] Carteira de vacinação
  [4] Histórico e ficha do animal
  [5] Sair
==================================================
Digite a opção desejada: 3

==================================================
        Consulta da carteira de vacinação.
--------------------------------------------------
ID: 1 | NOME: Thor | ESPÉCIE: Cachorro | TUTOR: Ana
ID: 2 | NOME: Mel | ESPÉCIE: Gato | TUTOR: João
--------------------------------------------------
ID do animal: 1
--------------------------------------------------
CARTEIRA DE THOR (tutor: Ana)
--------------------------------------------------
VACINA: V8 | DATA: 05/11/2026
VACINA: Antirrábica | DATA: 20/12/2026

Aperte Enter para voltar ao menu...
```

---

## 🧠 Como funciona por dentro

### Modelagem: três listas ligadas por ID

Todo o sistema gira em torno de um único dicionário, carregado na memória ao iniciar e gravado em disco a cada alteração:

```python
clinica = {
    "tutores": [],
    "animais": [],
    "procedimentos": []
}
```

Cada lista guarda dicionários, e o vínculo entre eles é feito por **ID**, do mesmo jeito que chaves estrangeiras funcionam num banco relacional:

```python
{"id": 1, "nome": "Ana", "telefone": "31999998888", "email": "ana@email.com"}

{"id": 1, "id_tutor": 1, "nome": "Thor", "especie": "Cachorro", "peso": 30.0}

{"id": 1, "id_animal": 1, "tipo": "Vacinação", "nome": "V8", "data": "2026-11-05"}
```

A decisão importante aqui foi **guardar o ID, não o objeto**. Em uma primeira versão, o animal guardava o dicionário inteiro do tutor — o que funcionava, mas duplicava a informação: ao editar o telefone do tutor, a cópia dentro do animal continuava desatualizada. Guardando só o número, existe uma única fonte de verdade, e o restante é buscado quando necessário.

### Geração de IDs

```python
def proximo_id(lista):
    if not lista:
        return 1
    return max(item["id"] for item in lista) + 1
```

O ID é o **maior existente + 1**, e não o tamanho da lista. A diferença aparece depois de uma exclusão: com os IDs 1, 4 e 7 cadastrados, `len() + 1` devolveria 4 — um ID que já existe, que corromperia os vínculos silenciosamente.

### Busca: a função que o CRUD inteiro reaproveita

```python
def buscar_id(lista, id_busca):
    for item in lista:
        if item["id"] == id_busca:
            return item
    return None
```

Ela não imprime nada e não decide nada: apenas encontra e devolve, ou devolve `None`. Essa separação é o que permite usar a mesma função para listar, editar, excluir e montar relatórios — em cada caso, quem chamou decide o que fazer com o resultado.

Como ela devolve a **referência** ao dicionário original (e não uma cópia), editar um tutor é direto:

```python
tutor_selecionado["nome"] = novo_nome
```

A alteração já reflete dentro da lista, sem precisar reinserir nada.

### Listagens: laços aninhados com filtro

Para mostrar cada tutor com seus animais, o laço externo percorre os tutores e o interno percorre **todos** os animais, imprimindo apenas os que pertencem ao tutor da iteração atual:

```python
for tutor in clinica["tutores"]:
    for animal in clinica["animais"]:
        if animal["id_tutor"] == tutor["id"]:
            ...
```

### Exclusão em cascata

Excluir um tutor sem tratar os vínculos deixaria **registros órfãos**: animais apontando para um tutor inexistente, e procedimentos apontando para esses animais. Qualquer tela de consulta quebraria ao tentar montar o nome do responsável.

A solução percorre três níveis, de baixo para cima — primeiro anota os IDs dos animais do tutor, depois descarta os procedimentos desses animais, então os animais, e por fim o tutor:

```python
procedimentos_restantes = []
for procedimento in clinica["procedimentos"]:
    if procedimento["id_animal"] not in ids_animais:
        procedimentos_restantes.append(procedimento)

clinica["procedimentos"] = procedimentos_restantes
```

Repare que a remoção **constrói uma lista nova com o que permanece**, em vez de remover itens da lista original durante a iteração. Remover enquanto se percorre faz o índice interno do laço avançar sobre elementos que deslizaram para trás, e alguns itens nunca chegam a ser avaliados — um bug que só se manifesta quando dois registros a excluir estão em posições consecutivas.

Antes de confirmar, o sistema informa o tamanho do estrago:

```
ATENÇÃO: este tutor possui 2 animal(is) e 5 procedimento(s) vinculados,
que também serão excluídos.
Tem certeza de que quer excluir? [S/N]:
```

### Datas: ISO no disco, brasileiro na tela

As datas são lidas no formato `dd/mm/aaaa`, validadas com `datetime.strptime` — que rejeita tanto formatos errados quanto datas inexistentes, como `31/02/2026` — e armazenadas em **ISO 8601** (`aaaa-mm-dd`).

O motivo é a ordenação. Em ISO, a ordem alfabética coincide com a ordem cronológica, então ordenar o histórico é trivial:

```python
encontrados.sort(key=lambda item: item.get("data", ""))
```

No formato brasileiro isso falharia: `05/12/2026` viria antes de `10/01/2026`, porque a comparação de texto olha o primeiro caractere. A conversão de volta para exibição acontece só na hora do `print`, via `formatar_data()`.

### Entrada de dados à prova de usuário

Toda leitura passa por uma função dedicada, e nenhuma delas deixa o programa seguir com dado inválido:

| Função | Garante |
|---|---|
| `ler_int()` | É um número inteiro; devolve `None` em caso de erro |
| `ler_texto()` | Não aceita campo vazio |
| `ler_telefone()` | Apenas dígitos, preservando zeros à esquerda |
| `ler_peso()` | Número decimal entre 0 e 500 kg; aceita vírgula ou ponto |
| `ler_data()` | Formato válido, data existente e não anterior a hoje |

O ponto central é que `try/except` sozinho não basta: capturar o `ValueError` e seguir em frente deixa a variável indefinida (`NameError`) ou, pior, carregando o **valor da iteração anterior** — um bug silencioso em que o programa executa uma opção que o usuário não escolheu. Por isso cada validação ou repete o laço até receber algo válido, ou devolve `None` para quem chamou decidir.

### Tipos de procedimento orientados a dados

Os cinco tipos de procedimento compartilham a mesma lógica e diferem em dois detalhes: o rótulo e se pedem ou não uma descrição. Em vez de cinco blocos quase idênticos, essa variação virou um dicionário de configuração:

```python
TIPOS_PROCEDIMENTO = {
    1: ("Vacinação", "nome da vacina"),
    2: ("Castração", None),
    3: ("Exame", "nome do exame"),
    4: ("Consulta", None),
    5: ("Cirurgia", "nome da cirurgia"),
}
```

O fluxo de agendamento é um só, e consulta esse mapa. Adicionar "Tosa" ao sistema é acrescentar uma linha — e, mais importante, mudar a regra de validação de data passa a ser uma alteração em um único lugar.

### Tolerância a falhas

- O carregamento captura `FileNotFoundError` **e** `json.JSONDecodeError`, então nem a primeira execução nem um arquivo corrompido impedem o programa de abrir.
- Chaves ausentes são recriadas com `setdefault()`, o que mantém arquivos de versões anteriores compatíveis.
- As telas de consulta toleram vínculos quebrados, exibindo `(tutor removido)` em vez de encerrar com erro.

---

## 🛠️ Conceitos aplicados

| Conceito | Onde aparece |
|---|---|
| **Listas de dicionários** | Estrutura principal de tutores, animais e procedimentos |
| **Funções com `return`** | `buscar_id`, `proximo_id`, `carregar_db`, leitores de entrada |
| **Parâmetros e escopo** | Funções recebem os dados em vez de acessar variáveis globais |
| **Laços aninhados** | Listagem de animais por tutor |
| **Padrão filtro** (`for` + `if`) | Procedimentos por animal, exclusão em cascata |
| **`while True` com `break`** | Menus e validação de entrada |
| **`try` / `except`** | Conversões numéricas, datas e leitura de arquivo |
| **Módulo `datetime`** | Validação, armazenamento e formatação de datas |
| **Módulo `json`** | Persistência com `dump` e `load` |
| **`with open()`** | Fechamento automático dos arquivos |
| **Integridade referencial** | Vínculos por ID e exclusão em cascata |

---

## 🚀 Como executar

É necessário apenas o **Python 3** instalado. Nenhuma dependência externa.

```bash
git clone https://github.com/0xluangabriel/vetsys-clinica.git
cd vetsys-clinica
python3 main.py
```

> No Windows, use `py main.py`.

O arquivo `clinica.json` é criado automaticamente no primeiro cadastro.

---

## 📌 Sobre

Projeto pessoal desenvolvido para pôr em prática os fundamentos de Python em um contexto próximo ao de um sistema real. O foco não foi apenas fazer funcionar, mas entender como e por que cada decisão foi tomada e no que ela influencia no resto do sistema.

Boa parte do que está documentado aqui nasceu de bugs reais encontrados durante o desenvolvimento e corrigidos depois de entender a causa.

Feito por **Luan Gabriel Alves da Silva** — [github.com/0xluangabriel](https://github.com/0xluangabriel)
