import csv
import re
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
import argparse
import logging

class QRCodeGenerator:
    def __init__(self, font_path="../fonts/ClashDisplay-Bold.ttf", 
                 central_size=125, padding=20, dpi=(750, 750),
                 log_level=logging.INFO):
        """
        Inicializa o gerador de QR Code com as configurações especificadas.
        
        :param font_path: Caminho para o arquivo da fonte.
        :param central_size: Tamanho da imagem central em pixels.
        :param padding: Espaço entre a imagem central e os módulos do QR Code.
        :param dpi: DPI para a imagem final.
        :param log_level: Nível de logging.
        """
        self.font_path = font_path
        self.central_size = central_size
        self.padding = padding
        self.dpi = dpi
        self.setup_logging(log_level)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def setup_logging(self, log_level):
        """
        Configura o sistema de logging.
        
        :param log_level: Nível de logging.
        """
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    
    def extract_table_number(self, long_url):
        """
        Extrai o número da mesa da URL longa.
        
        :param long_url: URL longa contendo o número da mesa.
        :return: Número da mesa como string ou None se não encontrado.
        """
        match = re.search(r'comanda%20(\d+)', long_url)
        if match:
            table_number = match.group(1)
            self.logger.debug(f"Extraído número da mesa: {table_number} de URL: {long_url}")
            return table_number
        self.logger.warning(f"Número da mesa não encontrado na URL: {long_url}")
        return None
    
    def create_central_image(self, table_number):
        """
        Cria a imagem central com cantos arredondados e texto de alta qualidade.
        
        :param table_number: Número da mesa a ser exibido.
        :return: Imagem PIL da imagem central.
        """
        scale_factor = 4
        high_res_size = self.central_size * scale_factor

        # Criar uma imagem de alta resolução com fundo transparente
        central_img_high_res = Image.new('RGBA', (high_res_size, high_res_size), (255, 255, 255, 0))

        # Criar um retângulo arredondado de alta resolução
        rounded_rect_high_res = Image.new('RGBA', (high_res_size, high_res_size), (255, 255, 255, 255))
        mask_high_res = Image.new('L', (high_res_size, high_res_size), 0)
        draw_mask_high_res = ImageDraw.Draw(mask_high_res)
        draw_mask_high_res.rounded_rectangle(
            [(0, 0), (high_res_size - 1, high_res_size - 1)],
            radius=20 * scale_factor,
            fill=255
        )

        # Aplicar a máscara para obter cantos arredondados
        rounded_rect_high_res.putalpha(mask_high_res)

        # Desenhar o texto na imagem de alta resolução
        draw_high_res = ImageDraw.Draw(rounded_rect_high_res)
        try:
            font_size = 36 * scale_factor
            font = ImageFont.truetype(self.font_path, font_size)
            self.logger.debug(f"Fonte carregada com tamanho: {font_size}")
        except IOError:
            self.logger.error(f"Fonte '{self.font_path}' não encontrada. Usando fonte padrão.")
            font = ImageFont.load_default()

        text = f"Mesa\n{table_number}"
        # Calcular a caixa delimitadora do texto para centralização
        bbox = draw_high_res.multiline_textbbox((0, 0), text, font=font, align='center')
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        position = ((high_res_size - text_width) // 2, (high_res_size - text_height) // 2)
        # Definir a cor do texto para #3269D0
        draw_high_res.multiline_text(position, text, font=font, fill="#3269D0", align='center')

        # Redimensionar a imagem central de alta resolução para o tamanho desejado com filtro de alta qualidade
        central_img = rounded_rect_high_res.resize((self.central_size, self.central_size), Image.LANCZOS)
        self.logger.debug(f"Imagem central criada com tamanho final: {self.central_size}px")
        return central_img
    
    def create_qr_code(self, short_url, table_number, output_file):
        """
        Cria um QR Code personalizado com a imagem central e salva no arquivo especificado.
        
        :param short_url: URL curta para codificar no QR Code.
        :param table_number: Número da mesa para a imagem central.
        :param output_file: Caminho para salvar o QR Code gerado.
        """
        try:
            # Gerar QR Code com alta correção de erros e border reduzido
            qr = qrcode.QRCode(
                version=None,  # Deixa o QR Code ajustar o tamanho automaticamente
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,    # Tamanho da caixa padrão
                border=2,       # Borda reduzida para diminuir espaço em branco
            )
            qr.add_data(short_url)
            qr.make(fit=True)  # Ajusta o tamanho do QR Code automaticamente
            self.logger.debug("QR Code gerado com sucesso.")

            img = qr.make_image(fill_color='black', back_color='white').convert('RGBA')

            # Criar a imagem central
            central_img = self.create_central_image(table_number)

            # Calcular o tamanho máximo permitido para a imagem central para manter o padding
            img_width, img_height = img.size
            max_central_size = min(img_width, img_height) - 2 * self.padding
            if self.central_size > max_central_size:
                self.logger.warning(f"Tamanho da imagem central ({self.central_size}px) excede o máximo permitido ({max_central_size}px). Redimensionando.")
                central_size = max_central_size
                central_img = self.create_central_image(table_number)
            else:
                central_size = self.central_size

            # Calcular a posição para colar a imagem central no QR Code
            central_width, central_height = central_img.size
            position = ((img_width - central_width) // 2, (img_height - central_height) // 2)

            # Colar a imagem central no QR Code usando a máscara alfa para preservar a transparência
            img.paste(central_img, position, central_img)
            self.logger.debug("Imagem central colada no QR Code.")

            # Salvar a imagem com DPI alto
            img.save(output_file, dpi=self.dpi)
            self.logger.info(f"QR Code salvo em: {output_file} com DPI: {self.dpi}")
        except Exception as e:
            self.logger.error(f"Erro ao criar QR Code para a mesa {table_number}: {e}")
    
    def process_csv(self, csv_file):
        """
        Processa o arquivo CSV e gera QR Codes para cada entrada válida.
        
        :param csv_file: Caminho para o arquivo CSV.
        """
        if not os.path.isfile(csv_file):
            self.logger.error(f"Arquivo CSV não encontrado: {csv_file}")
            return

        output_folder = "qr-codes"
        os.makedirs(output_folder, exist_ok=True)
        self.logger.info(f"Pasta de saída verificada/criada: {output_folder}")

        try:
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    long_url = row.get('longUrl', '').strip()
                    short_url = row.get('shortUrl', '').strip()
                    table_number = self.extract_table_number(long_url)

                    if table_number and short_url:
                        output_file = os.path.join(output_folder, f"qr-mesa-{table_number}.png")
                        self.create_qr_code(short_url, table_number, output_file)
                    else:
                        self.logger.warning(f"Dados inválidos para linha: {row}")
        except Exception as e:
            self.logger.error(f"Erro ao processar o arquivo CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gerar QR Codes personalizados a partir de um arquivo CSV.")
    parser.add_argument('csv_file', help='Caminho para o arquivo CSV')
    parser.add_argument('--font_path', default="../fonts/ClashDisplay-Bold.ttf",
                        help='Caminho para o arquivo da fonte (default: ../fonts/ClashDisplay-Bold.ttf)')
    parser.add_argument('--central_size', type=int, default=125,
                        help='Tamanho da imagem central em pixels (default: 125)')
    parser.add_argument('--padding', type=int, default=20,
                        help='Padding entre a imagem central e os módulos do QR Code (default: 20)')
    parser.add_argument('--dpi', type=int, nargs=2, default=(750, 750),
                        help='DPI para a imagem final (default: 750 750)')
    parser.add_argument('--log_level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Nível de logging (default: INFO)')

    args = parser.parse_args()

    # Convert log_level string to logging constant
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)

    qr_generator = QRCodeGenerator(
        font_path=args.font_path,
        central_size=args.central_size,
        padding=args.padding,
        dpi=tuple(args.dpi),
        log_level=log_level
    )

    qr_generator.process_csv(args.csv_file)

if __name__ == "__main__":
    main()
