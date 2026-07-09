# Domain (Especificações e Contratos)

## Objetivo
O coração do nosso Spec-Driven Development. Este diretório contém apenas **Interfaces, Protocolos (typing.Protocol) e Classes Abstratas (ABC)**. 
Ele não deve conter implementações concretas (acesso a rede, banco de dados ou APIs de terceiros).

## Arquivos e Responsabilidades
- **`interfaces.py`**: Define os contratos estritos que o resto do sistema **DEVE** seguir. Contém as assinaturas do `YampiClientProtocol`, `MessageProviderProtocol` e `StateRepositoryProtocol`. O sistema se comunica através dessas interfaces.

## 🚨 Diretiva de Manutenção (Para IA)
> [!IMPORTANT]
> Se você modificar os contratos aqui ou adicionar novas interfaces, **DEVE**:
> 1. Garantir que todas as implementações concretas (em `core` ou `ports`) sejam atualizadas para respeitar a nova assinatura.
> 2. Atualizar este arquivo `README.md` para explicar o propósito do novo contrato.
