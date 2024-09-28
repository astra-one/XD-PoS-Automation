# Ideia Inicial

Realizar o input de uma lista de pedidos como por exemplo:

Chopp Brahma 2x 25,00
Chopp Heineken 1x 30,00
Chopp Brahma 1x 12,50

Valor Total com Serviço R$ 82,50

O código deverá unificar todos os pedidos iguais e somar a quantidade e o valor total. Para o caso de pedidos que tiverem mais que duas unidades, o valor unitário deverá ser calculado.

Deverá retornar uma mensagem formatada.

Construir também um fluxo de fechamento de pedido, que irá receber como input os pedidos, retornar a comanda processada e depois perguntar a gorjeta extra.

# Chains

1. Serialização de Pedidos

Será inputado em formato de texto, está chain deverá transformar em JSON seguindo o padrão de campos. Ao final deverá ter como resultado a comanda processada.

2. Calculo de Valores e Taxas de Serviço

Deverá calcular o valor total da comanda, somar a taxa de serviço e retornar a mensagem formatada.

3. Formatação de Mensagem

Não terá inteligência, apenas irá formatar a mensagem de acordo com o padrão.