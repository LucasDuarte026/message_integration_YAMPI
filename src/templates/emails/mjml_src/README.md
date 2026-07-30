# Guia de Templates MJML

Este diretório (`src/templates/emails/mjml_src/`) contém o código-fonte original dos e-mails da Eleveme usando o framework **MJML**.

## Por que MJML?
No passado, construíamos os e-mails com HTML/CSS em linha manual (Jinja2 cru), o que dificultava o suporte a diferentes clientes de e-mail (Outlook, Gmail, Apple Mail) e quebrava o layout móvel constantemente. O [MJML](https://mjml.io/) é uma linguagem de marcação projetada especificamente para e-mails responsivos que compila para o HTML à prova de falhas exigido pelos clientes de e-mail. 

## Como funciona no nosso Backend
Nosso sistema ainda usa **Jinja2** na etapa final (durante o envio pelo Worker Python), mas ele renderiza os arquivos `.html` que foram compilados a partir do `.mjml`.
A pipeline é:
1. Você cria/edita um arquivo `nome_do_template.mjml`.
2. Você compila esse arquivo. Ele gera `nome_do_template.html` na pasta `src/templates/emails/`.
3. O Backend (Python Jinja2) lê `nome_do_template.html` em tempo de execução e insere os dados do cliente e os dados do `brand_data.yml`.

## Central de Dados (brand_data.yml)
A maioria dos textos descritivos, as URLs das redes sociais e configurações da empresa não estão fixas nos templates. Elas vivem no `brand_data.yml` (uma pasta acima, em `src/templates/emails/`). 
Isso permite alterar o WhatsApp do suporte ou um copy de um cupom sem precisar recompilar todo o HTML.

## Como instalar e compilar MJML

Requisitos: Ter o `node` e `npm` instalados.

Se você modificar um arquivo `.mjml`, deve compilá-lo para que as alterações reflitam em produção. Do diretório raiz do seu projeto, execute:

```bash
npx mjml src/templates/emails/mjml_src/*.mjml -o src/templates/emails/
```

Isso pegará todos os MJMLs e cuspirá as versões HTML na pasta superior.

## Como gerar Mocks Locais e Testar o Design

Para visualizar os e-mails localmente no navegador **antes de subir para produção**, use o nosso script gerador de Mocks. Ele simula o Jinja2 inserindo dados fictícios (e lendo do `brand_data.yml`) para renderizar as versões finais:

Estando na raiz do projeto (se tiver o ambiente python ativado):
```bash
python src/templates/emails/mjml_src/email_mock_generator.py
```
Isso criará uma pasta `/mocks/` dentro de `src/templates/emails/` contendo arquivos HTML que você pode abrir em qualquer navegador (ex: `mock_pedido_aprovado.html`).

## Regras de Componentes e Assets
- Use as cores da marca.
- O arquivo `components/styles.mjml` contém as classes utilitárias compartilhadas, como as classes para sombras (ex: `.btn-shadow-blue`). Use com o `css-class` nas tags `<mj-button>`.
- Não coloque emojis soltos dentro do texto de botões, para evitar quebra de layout no iOS/Outlook.
- **Assets Visuais:** As imagens locais dos e-mails estão estritamente organizadas em uma estrutura de pastas sequenciais (de `images/email_1_...` a `images/email_9_...`). Cada template tem sua subpasta com `header/` e `body/`. Arquivos não devem conter caracteres especiais como `%` (isso quebra os links do navegador no mock).
