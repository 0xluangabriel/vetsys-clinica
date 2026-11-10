# VetSys — Sistema de Gestão para Clínicas Veterinárias

Sistema de linha de comando em Python puro, sem dependências externas, para cadastro de tutores e animais, agendamento de procedimentos, carteira de vacinação e histórico clínico. Modela dados relacionais sem banco de dados, usando listas de dicionários ligadas por ID e persistência em JSON.

---

## Funcionalidades

- **Tutores e animais:** CRUD completo, com ID gerado automaticamente e cada animal vinculado a um tutor.
- **Exclusão em cascata:** remove o tutor, seus animais e os procedimentos vinculados, informando antes quantos registros serão afetados.
- **Procedimentos:** agendamento e edição de cinco tipos (Vacinação, Castração, Exame, Consulta e Cirurgia), com validação de data.
- **Consultas:** carteira de vacinação e histórico clínico em ordem cronológica, além da ficha do animal com o tutor e o total de procedimentos.
- **Persistência:** salvamento automático em `clinica.json` a cada alteração e carregamento na inicialização.

---

## Exemplo de uso

```
==================================================
                      VetSys
==================================================
  [1] Cadastro de animais e tutores
  [2] Agendamento de procedimentos
  [3] Carteira de vacinação
  [4] Histórico e ficha do animal
  [5] Sair
==================================================
Digite a opção desejada: 3
--------------------------------------------------
ID: 1 | NOME: Thor | ESPÉCIE: Cachorro | TUTOR: Ana
ID: 2 | NOME: Mel | ESPÉCIE: Gato | TUTOR: João
--------------------------------------------------
ID do animal: 1
CARTEIRA DE THOR (tutor: Ana)
VACINA: V8 | DATA: 05/11/2026
VACINA: Antirrábica | DATA: 20/12/2026
```

---

## Decisões técnicas

### Modelagem relacional por ID
Os dados ficam em um dicionário com três listas (`tutores`, `animais`, `procedimentos`), ligadas por ID como chaves estrangeiras:

```python
{"id": 1, "id_tutor": 1, "nome": "Thor", "especie": "Cachorro", "peso": 30.0}
{"id": 1, "id_animal": 1, "tipo": "Vacinação", "nome": "V8", "data": "2026-11-05"}
```

Armazenar o ID, e não uma cópia do objeto, mantém uma única fonte de verdade: editar o telefone do tutor atualiza o dado em todo o sistema.

### Geração de IDs
O próximo ID é `max(id) + 1`, e não `len(lista) + 1`. Depois de exclusões, `len()` pode devolver um ID já existente e corromper os vínculos.

```python
def proximo_id(lista):
    return max((item["id"] for item in lista), default=0) + 1
```

### Busca reutilizável
`buscar_id()` só encontra e devolve o registro (ou `None`), sem imprimir nem decidir nada. Por isso, a mesma função atende listagem, edição, exclusão e relatórios. Como ela devolve a referência ao dicionário original, a edição altera a lista diretamente.

### Exclusão em cascata sem registros órfãos
A exclusão percorre três níveis: procedimentos, animais e, por fim, o tutor. Para remover, o código constrói uma lista nova com os itens que permanecem, em vez de remover durante a iteração, o que pularia elementos consecutivos.

```python
clinica["procedimentos"] = [p for p in clinica["procedimentos"] if p["id_animal"] not in ids_animais]
```

### Datas em ISO 8601
A entrada é lida em `dd/mm/aaaa`, validada com `datetime.strptime`, que rejeita datas inexistentes como `31/02/2026`, e armazenada como `aaaa-mm-dd`. Nesse formato, a ordem alfabética coincide com a cronológica, então o histórico é ordenado com um único `sort()`. A conversão para o formato brasileiro ocorre apenas na exibição.

### Validação centralizada de entrada
Cada tipo de dado tem uma função de leitura própria, que repete a pergunta até receber um valor válido ou devolve `None`. Assim, nenhum valor inválido, ou de uma iteração anterior, segue adiante.

| Função | Garante |
|---|---|
| `ler_int()` | Número inteiro válido |
| `ler_texto()` | Campo não vazio |
| `ler_telefone()` | Apenas dígitos, preservando zeros à esquerda |
| `ler_peso()` | Decimal entre 0 e 500 kg, com vírgula ou ponto |
| `ler_data()` | Data existente e não anterior a hoje |

### Configuração orientada a dados
Os tipos de procedimento ficam em um dicionário de configuração, em vez de cinco blocos de código duplicados:

```python
TIPOS_PROCEDIMENTO = {
    1: ("Vacinação", "nome da vacina"),
    2: ("Castração", None),
    3: ("Exame", "nome do exame"),
    4: ("Consulta", None),
    5: ("Cirurgia", "nome da cirurgia"),
}
```

Adicionar um novo tipo exige uma linha, e as regras de validação ficam centralizadas em um único fluxo.

### Tolerância a falhas
- **Carregamento seguro:** o programa captura `FileNotFoundError` e `json.JSONDecodeError`, então abre mesmo sem arquivo ou com arquivo corrompido.
- **Compatibilidade:** `setdefault()` recria chaves ausentes, mantendo arquivos de versões anteriores compatíveis.
- **Vínculos quebrados:** as consultas exibem `(tutor removido)` em vez de encerrar com erro.

---

## Conceitos aplicados

Listas de dicionários, funções com retorno, laços aninhados, padrão filtro (`for` + `if`), `while True` com `break`, `try`/`except`, módulos `datetime` e `json`, gerenciador de contexto (`with open()`) e integridade referencial.

---

## Como executar

Requer apenas Python 3.

```bash
git clone https://github.com/0xluangabriel/vetsys-clinica.git
cd vetsys-clinica
python3 main.py
```

No Windows, use `py main.py`. O arquivo `clinica.json` é criado no primeiro cadastro.

---

Desenvolvido por **Luan Gabriel Alves da Silva** — [github.com/0xluangabriel](https://github.com/0xluangabriel)
