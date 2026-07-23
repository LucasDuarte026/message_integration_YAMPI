# Domain (Especificações e Contratos)

## Objetivo
O coração do nosso Spec-Driven Development. Este diretório contém apenas **Interfaces, Protocolos (typing.Protocol) e Classes Abstratas (ABC)**. 
Ele não deve conter implementações concretas (acesso a rede, banco de dados ou APIs de terceiros).

## Arquivos e Responsabilidades
- **`interfaces.py`**: Define os contratos estritos que o resto do sistema **DEVE** seguir. Contém as assinaturas do `YampiClientProtocol`, `MessageProviderProtocol` e `StateRepositoryProtocol`. O sistema se comunica através dessas interfaces.

## 🚨 Diretiva de Manutenção (Para IA e Desenvolvedores)
> [!IMPORTANT]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> Se você modificar os contratos aqui ou adicionar novas interfaces, **DEVE**:
> 1. Garantir que todas as implementações concretas (em `core` ou `ports`) sejam atualizadas para respeitar a nova assinatura.
> 2. Atualizar este arquivo `README.md` para explicar o propósito do novo contrato.

## Dependências
- **Nenhuma**: O `domain` é a camada mais interna e pura da aplicação. Ele não depende de nenhuma outra pasta (core, ports, workers) e nem de bibliotecas externas (exceto recursos nativos de tipagem do Python como `typing` e `abc`).

## Future Updates (Pontos a serem modificados e melhorados)
- Evoluir os Protocolos para definir não apenas assinaturas de métodos, mas especificar também as classes de dados de resposta (Data Transfer Objects - DTOs) nativos (ex: Usar `dataclasses` ou `Pydantic` para padronizar o retorno dos métodos do cliente Yampi no nível de Domínio).
- Documentar de forma nativa e estrita (via Docstrings nas interfaces) quais *Exceptions* devem ser lançadas e esperadas pelas camadas superiores para reforçar a robustez do tratamento de falhas.
