import os
import sys
from jinja2 import Environment, FileSystemLoader

# Adicionar a raiz do projeto ao sys.path se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

def generate_mock(template_name, mock_data, output_name):
    # Configurar Jinja2
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, "html_compiled")
    
    output_dir = os.path.join(
        current_dir,
        "mocks"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Gerando mock para {template_name}...")
    
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    
    try:
        template = env.get_template(template_name)
    except Exception as e:
        print(f"Erro ao carregar o template {template_name}: {e}")
        print("Lembre-se de compilar o MJML primeiro: npx mjml src/templates/emails/mjml/views/*.mjml -o src/templates/emails/html_compiled/")
        return
        
    html_output = template.render(**mock_data)
    
    output_path = os.path.join(output_dir, output_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
        
    print(f"✅ Mock gerado com sucesso em: {output_path}")

if __name__ == "__main__":
    # Mock data baseada nas regras de negócio e no brand_data.yml
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Criar URLs no formato file:/// para funcionar no browser local
    def to_file_url(path):
        return "file://" + path.replace("\\", "/")
        
    # Encontrar qualquer imagem na pasta independente da extensão
    def find_image(folder_path, prefix=None):
        if not os.path.exists(folder_path):
            return "https://via.placeholder.com/600x400?text=Folder+Not+Found"
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                if prefix and not file.lower().startswith(prefix.lower()):
                    continue
                return to_file_url(os.path.join(folder_path, file))
        return "https://via.placeholder.com/600x400?text=No+Image"
    
    # Caminho para os assets
    ref_dir = os.path.join(base_dir, "src", "templates", "emails", "assets", "images")
    
    # Mocks definitions
    mocks = [
        {
            "template": "pedido_aprovado.html",
            "output": "mock_pedido_aprovado.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "order_number": "#10948",
                "header_image_url": find_image(os.path.join(ref_dir, "email_1_pedido_aprovado", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_1_pedido_aprovado", "body")),
                "tracking_url": "https://elevemeloja.com.br",
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "pedido_a_caminho.html",
            "output": "mock_pedido_a_caminho.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "order_number": "#10948",
                "tracking_code": "BR987654321BR",
                "tracking_url": "https://elevemeloja.com.br/rastreamento",
                "header_image_url": find_image(os.path.join(ref_dir, "email_3_pedido_a_caminho", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_3_pedido_a_caminho", "body")),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "pedido_pendente.html",
            "output": "mock_pedido_pendente.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "order_number": "#10948",
                "pix_code": "00020126580014BR.GOV.BCB.PIX0136123e4567-e89b-12d3-a456-4266141740005204000053039865405150.005802BR5913Eleveme Store6008SAO PAULO62070503***6304E2CA",
                "checkout_url": "https://elevemeloja.com.br/checkout/pay/10948",
                "header_image_url": find_image(os.path.join(ref_dir, "email_2_pedido_pendente", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_2_pedido_pendente", "body")),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail"),
                "items_html": """
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #334155; font-weight: 700;">Serum Revitalizante Noturno</td>
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #475569; text-align: center;">1</td>
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #334155; font-weight: 700; text-align: right;">R$ 150.00</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #334155; font-weight: 700;">Gummy Vitamínico</td>
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #475569; text-align: center;">1</td>
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #334155; font-weight: 700; text-align: right;">R$ 100.00</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0; color: #64748b;">
            <td style="padding: 10px 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 13px;">Frete</td>
            <td style="padding: 10px 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 13px; text-align: center;">-</td>
            <td style="padding: 10px 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 13px; text-align: right;"><s style="color: #94A3B8;">R$ 23.50</s> <span style="color: #10B981; font-weight: bold;">Grátis</span></td>
        </tr>
        <tr style="background-color: #e2e8f0; font-weight: 700;">
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #1e3a8a;">Total do Pedido</td>
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #1e3a8a; text-align: center;">-</td>
            <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #1e3a8a; text-align: right;">R$ 250.00</td>
        </tr>
                """
            }
        },
        {
            "template": "cupom_pedido_1.html",
            "output": "mock_cupom_pedido_1.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "order_number": "#10948",
                "coupon_code": "ELEVE10",
        "value_cupom": "10",
                "store_url": "https://elevemeloja.com.br",
                "header_image_url": find_image(os.path.join(ref_dir, "email_4_cupom_pedido_1", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_4_cupom_pedido_1", "body"), prefix="10_off"),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "cupom_pedido_2.html",
            "output": "mock_cupom_pedido_2.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "order_number": "#10948",
                "coupon_code": "ELEVE15",
        "value_cupom": "15",
                "store_url": "https://elevemeloja.com.br",
                "header_image_url": find_image(os.path.join(ref_dir, "email_5_cupom_pedido_2", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_5_cupom_pedido_2", "body"), prefix="5_desconto"),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "cupom_pedido_3.html",
            "output": "mock_cupom_pedido_3.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "order_number": "#10948",
                "coupon_code": "ELEVE20",
        "value_cupom": "20",
                "store_url": "https://elevemeloja.com.br",
                "header_image_url": find_image(os.path.join(ref_dir, "email_6_cupom_pedido_3", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_6_cupom_pedido_3", "body"), prefix="5_primeira"),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "carrinho_abandonado_cupom4.html",
            "output": "mock_carrinho_abandonado_cupom4.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "coupon_code": "ELEVEME10",
        "value_cupom": "10",
                "simulate_url": "https://elevemeloja.com.br/checkout/cart?recover=10&coupon=ELEVEME10",
                "header_image_url": find_image(os.path.join(ref_dir, "email_7_carrinho_abandonado_4", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_7_carrinho_abandonado_4", "body")),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "carrinho_abandonado_cupom5.html",
            "output": "mock_carrinho_abandonado_cupom5.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "coupon_code": "CART15",
        "value_cupom": "15",
                "simulate_url": "https://elevemeloja.com.br/checkout/cart?recover=15&coupon=CART15",
                "header_image_url": find_image(os.path.join(ref_dir, "email_8_carrinho_abandonado_5", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_8_carrinho_abandonado_5", "body")),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        },
        {
            "template": "carrinho_abandonado_cupom6.html",
            "output": "mock_carrinho_abandonado_cupom6.html",
            "data": {
                "customer_name": "Lucas Duarte",
                "coupon_code": "CART20",
        "value_cupom": "20",
                "simulate_url": "https://elevemeloja.com.br/checkout/cart?recover=20&coupon=CART20",
                "header_image_url": find_image(os.path.join(ref_dir, "email_9_carrinho_abandonado_6", "header")),
                "body_image_url": find_image(os.path.join(ref_dir, "email_9_carrinho_abandonado_6", "body")),
                "instagram_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="instagram"),
                "facebook_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="facebook"),
                "whatsapp_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="whatsapp"),
                "contact_mail_icon_url": find_image(os.path.join(ref_dir, "social_icons"), prefix="contact-mail")
            }
        }
    ]
    
    for mock in mocks:
        generate_mock(mock["template"], mock["data"], mock["output"])
