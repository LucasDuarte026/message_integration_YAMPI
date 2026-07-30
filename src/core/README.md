# Core (Infraestrutura Base)

## Objetivo
O diretório `core` abriga os componentes básicos de infraestrutura interna que suportam a aplicação. São os componentes que lidam com estado interno, configurações e nossa própria fonte de dados primária (API Yampi).

## Arquivos e Responsabilidades
- **`config.py`**: Gerenciador centralizado de variáveis de ambiente e credenciais. Garante a segurança retirando dados sensíveis do restante do código.
- **`client.py`**: O cliente robusto `YampiClient`. Implementa as requisições HTTP, paginação, fallback, rate limits e autenticação para consumir a API da Yampi.
- **`db.py`**: Implementação concreta em SQLite do repositório de persistência (`StateRepositoryProtocol`). Serve para salvar o estado da aplicação (ex: controle de disparo de mensagens duplicadas).
- **`macros.py`**: Arquivo de configurações de constantes e macros de negócios. Define *timers* para STG (Pedidos) e STC (Carrinhos), definindo horas para disparos de cupons, tempos limite e intervalos de workers.

## 🚨 Diretiva de Manutenção (Para IA e Desenvolvedores)
> [!IMPORTANT]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> Se você modificar, adicionar ou remover qualquer arquivo de infraestrutura neste diretório, **DEVE** atualizar este arquivo `README.md` imediatamente para refletir essas mudanças arquiteturais.

## Dependências
- **Nenhuma no Nível de Regras de Negócio**: O `core` não depende de workers ou ports (embora instancie a conexão HTTP que as interfaces definem).
- **Externas**: Bibliotecas como `requests` para requisições HTTP, biblioteca nativa do `sqlite3` e gerência de variáveis de ambiente.

## Future Updates (Pontos a serem modificados e melhorados)
- Expandir o `client.py` para suportar *Retries* exponenciais usando bibliotecas como `tenacity` em caso de instabilidade na Yampi.
- Migrar o `db.py` de SQLite para uma solução mais escalável via ORM assíncrono (ex: SQLAlchemy ou Tortoise ORM) caso o deploy se torne Serverless, o que impediria o uso fácil de um banco de dados em arquivo local.
- Adicionar validações mais robustas no `config.py` (usando pydantic) no carregamento das variáveis de ambiente.
