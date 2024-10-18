# Automatização da Comunicação do PDV - TCP

## Coti Automation - Antônio Martins

### 1. Objetivo

Este documento é um resumo das principais funções utilizadas pelo aplicativo XDOrders para Android, no momento de realizar a comunicação entre a aplicação e o PDV. Como resultado final, será gerado um Framework em Python, realizando a tradução do código em Java, e testando o funcionamento, buscando automatizar o MVP da Coti.

#### 1.1. Funcionalidades Necessárias

1. **Autenticação no PDV:** É necessário realizar a autenticação no PDV utilizando o usuário de ID 1 com uma credencial pré definida.
2. **Busca de Comandas:** É necessário realizar a busca de comandas no PDV, utilizando o usuário de ID 1, está busca deverá retornar todos os itens pedidos na comanda.
3. **Pagamento da Comanda:** Antes do fechamento da comanda, é necessário colocá-la em estado de pagamento, utilizando o usuário de ID 1.
4. **Fechamento de Comanda:** É necessário realizar o fechamento de uma comanda no PDV, utilizando o usuário de ID 1, está ação deverá fechar a comanda e liberar a mesa.

### Arquitetura

A comunicação entre o PDV e o aplicativo XDOrders é realizada através de uma conexão TCP, construida manualmente pela equipe de desenvolvimento do Software. Como base foi utilizado o arquivo `RestAdapter.java` disponível no diretório `/retrofit`. O arquivo `SecuredRestBuilder.java` utiliza desta estrutura já criada, para aperfeiçoar e customizar a comunicação, principalmente o processo de autenticação.

O envio dos pacotes TCP ocorre de acordo com o padrão descrito no arquivo `NetworkLanguage.java`, utilizando os seguintes Tokens:

```java
  private static final String ERROR_DESCRIPTION_PARAMETER = "ERRORDESCRIPTION";
  private static final String ERROR_ID_PARAMETER = "ERRORID";
  private static final String KEY_APPLICATION_VERSION = "APPVERSION";
  private static final String KEY_LICENSE = "LICENSE";
  private static final String KEY_MESSAGE_GENERIC_ERROR = "MESSAGEERROR";
  private static final String KEY_MESSAGE_ID = "MESSAGEID";
  private static final String KEY_MESSAGE_OK = "MESSAGEOK";
  private static final String KEY_MESSAGE_SERVER_NOT_AUTHORIZED = "NOTAUTHORIZED";
  private static final String KEY_MESSAGE_TYPE = "MESSAGETYPE";
  private static final String KEY_PENDING_MESSAGES = "MESSAGES";
  private static final String KEY_PROTOCOL_VERSION_IDENTIFIER = "PROTOCOLVERSION";
  private static final String KEY_SERVER_DISCONNECTED = "SERVERDISCONNECTED";
  private static final String KEY_SERVER_IDENTIFIER = "SERVERIDENTIFIER";
  private static final String KEY_SYNC_VERSION_IDENTIFIER = "SYNCVERSION";
  private static final String KEY_TOKEN = "TOKEN";
  private static final String KEY_USER_ID = "USERID";
  private static final String NEW_MESSAGE_END_OF_MESSAGE = "[EOM]";
  private static final String NEW_MESSAGE_PARAMETER_KEY = "[NP]";
  private static final String NEW_MESSAGE_PARAMETER_VALUE = "[EQ]";
```

O arquivo `TCPClient.java` é responsável por gerenciar a comunicação TCP, implementando métodos como envio e recebimento de pacotes para outros IPs da rede externa.

### Dificuldades

1. **Protocolo de Mensagens:** Entender o protocolo de mensagens, e em quais momentos cada mensagem deve ser enviada, e principalmente, como ela deverá ser construida é uma das maiores dificuldades deste projeto. A comunicação entre o PDV e o aplicativo XDOrders é realizada através de mensagens, que devem ser enviadas em um formato específico, e com um conteúdo específico.


### Arquivos Principais

Mensagem Inicial:

```
GETBOARDCONTENT
[NP]PROTOCOLVERSION[EQ]1
[NP]BOARDID[EQ]50
[NP]TYPE[EQ]1
[NP]USERID[EQ]1
[NP]TOKEN[EQ]0f291e94973f249beca6bbf16fbeb53e6ea38aba
[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetBoardInfoMessage
[NP]MESSAGEID[EQ]e777b2af-72c7-4e95-a1d2-548b8151dcfe[EOM]
```

Está mensagem é criada a partir do arquivo `GetBoardInfoMessage.java`, e é enviada para o PDV, solicitando informações sobre a Comanda.

#### `GetBoardInfoMessage.java`

A partir da coleta de pacotes realizada, é possível saber que os parametros:

1. type = 1
2. userId = 1
3. token = 0f291e94973f249beca6bbf16fbeb53e6ea38aba

Não sabemos ainda, como é feita a geração deste token, provavelmente é gerado a partir de um algoritmo de criptografia e de forma dinâmica.

Neste arquivo existem as seguintes funções:

```java
  public DeliverableMessage MakeDeliverable()
  {
    DeliverableMessage localDeliverableMessage = new DeliverableMessage();
    String str = NetworkMessageUtils.INSTANCE.IdentifyMessage(Grammar.INSTANCE.getGET_BOARD_CONTENT_IDENTIFIER());
    this.messageString = str;
    if (str == null) {
      Intrinsics.throwUninitializedPropertyAccessException("messageString");
    }
    str = str + NetworkMessageUtils.INSTANCE.AddProtocolVersion(this.protocolVersion);
    this.messageString = str;
    if (str == null) {
      Intrinsics.throwUninitializedPropertyAccessException("messageString");
    }
    StringBuilder localStringBuilder = new StringBuilder().append(str);
    NetworkMessageUtils localNetworkMessageUtils = NetworkMessageUtils.INSTANCE;
    str = Grammar.INSTANCE.getBOARD_ID_PARAMETER();
    Long localLong = this.boardId;
    if (localLong == null) {
      Intrinsics.throwNpe();
    }
    str = localNetworkMessageUtils.AddMessageParameter(str, Long.toString(localLong.longValue()));
    this.messageString = str;
    if (str == null) {
      Intrinsics.throwUninitializedPropertyAccessException("messageString");
    }
    str = str + NetworkMessageUtils.INSTANCE.AddMessageParameter(Grammar.INSTANCE.getTYPE_PARAMETER(), this.type);
    this.messageString = str;
    if (str == null) {
      Intrinsics.throwUninitializedPropertyAccessException("messageString");
    }
    str = str + NetworkMessageUtils.INSTANCE.AddMessageParameter(NetworkLanguage.INSTANCE.getKEY_USER_ID(), this.userId);
    this.messageString = str;
    if (str == null) {
      Intrinsics.throwUninitializedPropertyAccessException("messageString");
    }
    this.messageString = (str + NetworkMessageUtils.INSTANCE.AddMessageParameter(NetworkLanguage.INSTANCE.getKEY_TOKEN(), this.token));
    localDeliverableMessage.AddMessage(GetBoardInfoMessage.class, (INetworkMessage)this);
    return localDeliverableMessage;
  }
```

Está é a função responsável por construir a mensagem que será entregue, aprofundando um pouco mais nela, e utilizando a mensagem inicial como exemplo.

1. Construção de Identificador:

```java
String str = NetworkMessageUtils.INSTANCE.IdentifyMessage(Grammar.INSTANCE.getGET_BOARD_CONTENT_IDENTIFIER());
```

Acima é chamada uma função que irá retornar o identificador da API de busca por comandas, neste caso `GETBOARDCONTENT`.

2. Adição de Versão do Protocolo:

```java
str = str + NetworkMessageUtils.INSTANCE.AddProtocolVersion(this.protocolVersion);
```

Aqui é adicionado a versão do protocolo, que no caso é `1`.

3. Adição de Parâmetros:

```java
str = str + NetworkMessageUtils.INSTANCE.AddMessageParameter(Grammar.INSTANCE.getTYPE_PARAMETER(), this.type);
```

Aqui é adicionado o parâmetro `TYPE` com o valor `1`.

4. Adição de Parâmetros:

```java
str = str + NetworkMessageUtils.INSTANCE.AddMessageParameter(NetworkLanguage.INSTANCE.getKEY_USER_ID(), this.userId);
```

Aqui é adicionado o parâmetro `USERID` com o valor `1`. Aparentemente é referente ao usuário do Fernando.

5. Adição de Parâmetros:

```java
this.messageString = (str + NetworkMessageUtils.INSTANCE.AddMessageParameter(NetworkLanguage.INSTANCE.getKEY_TOKEN(), this.token));
```

Aqui é adicionado o parâmetro `TOKEN` com o valor `0f291e94973f249beca6bbf16fbeb53e6ea38aba`.

6. Adição de Mensagem:

```java
localDeliverableMessage.AddMessage(GetBoardInfoMessage.class, (INetworkMessage)this);
```

Aqui é adicionado a mensagem ao pacote que será enviado.

### Exemplos de Requisições

#### Exemplo 1 - Busca de Produtos Específicos

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemFamily[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]db45856c-b3fe-4995-a5fc-f08b09369904[EOM]
```

**Response**
```
POSTDATALIST[NP]OBJECT[EQ]Ww0KICB7DQogICAgImlkIjogMSwNCiAgICAibmFtZSI6ICJFTlRSQURBUyIsDQogICAgInBhcmVudElkIjogMCwNCiAgICAidmlzaWJsZSI6IHRydWUNCiAgfSwNCiAgew0KICAgICJpZCI6IDMsDQogICAgIm5hbWUiOiAiQ09SVEVTIFBBUlJJTExFUk8iLA0KICAgICJwYXJlbnRJZCI6IDAsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiA3LA0KICAgICJuYW1lIjogIlBSQVRPUyIsDQogICAgInBhcmVudElkIjogMCwNCiAgICAidmlzaWJsZSI6IHRydWUNCiAgfSwNCiAgew0KICAgICJpZCI6IDEyLA0KICAgICJuYW1lIjogIlNPQlJFTUVTQVMiLA0KICAgICJwYXJlbnRJZCI6IDAsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAxMywNCiAgICAibmFtZSI6ICJCRUJJREFTIiwNCiAgICAicGFyZW50SWQiOiAwLA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogMTQsDQogICAgIm5hbWUiOiAiREVTVElMQURPUyIsDQogICAgInBhcmVudElkIjogMCwNCiAgICAidmlzaWJsZSI6IHRydWUNCiAgfSwNCiAgew0KICAgICJpZCI6IDE1LA0KICAgICJuYW1lIjogIkNFUlZFSkFTIiwNCiAgICAicGFyZW50SWQiOiAwLA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogMTYsDQogICAgIm5hbWUiOiAiRFJJTktTIiwNCiAgICAicGFyZW50SWQiOiAwLA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogMTcsDQogICAgIm5hbWUiOiAiVklOSE9TL0VTUFVNQU5URSIsDQogICAgInBhcmVudElkIjogMCwNCiAgICAidmlzaWJsZSI6IHRydWUNCiAgfSwNCiAgew0KICAgICJpZCI6IDE4LA0KICAgICJuYW1lIjogIkVTUEVUSU5IT1MiLA0KICAgICJwYXJlbnRJZCI6IDMsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAyMCwNCiAgICAibmFtZSI6ICJOw4NPIFVTQVIiLA0KICAgICJwYXJlbnRJZCI6IDIxLA0KICAgICJ2aXNpYmxlIjogZmFsc2UNCiAgfSwNCiAgew0KICAgICJpZCI6IDIxLA0KICAgICJuYW1lIjogIkNPTVBMRU1FTlRPUyIsDQogICAgInBhcmVudElkIjogMCwNCiAgICAidmlzaWJsZSI6IGZhbHNlDQogIH0sDQogIHsNCiAgICAiaWQiOiAyOCwNCiAgICAibmFtZSI6ICJFbnRyYWRhIFhNTCIsDQogICAgInBhcmVudElkIjogMCwNCiAgICAidmlzaWJsZSI6IGZhbHNlDQogIH0sDQogIHsNCiAgICAiaWQiOiAyOSwNCiAgICAibmFtZSI6ICJTVUNPUyIsDQogICAgInBhcmVudElkIjogMTMsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzMCwNCiAgICAibmFtZSI6ICJXSElTS1kiLA0KICAgICJwYXJlbnRJZCI6IDE0LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogMzEsDQogICAgIm5hbWUiOiAiRFJJTksgU0VNIEFMQ09PTCIsDQogICAgInBhcmVudElkIjogMTMsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzMiwNCiAgICAibmFtZSI6ICJET1NFIEFQRVJJVElWTyIsDQogICAgInBhcmVudElkIjogMTQsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzMywNCiAgICAibmFtZSI6ICJWT0RLQSIsDQogICAgInBhcmVudElkIjogMTQsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzNCwNCiAgICAibmFtZSI6ICJHQVJSQUZBUyIsDQogICAgInBhcmVudElkIjogMTQsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzNSwNCiAgICAibmFtZSI6ICJDT01CTyIsDQogICAgInBhcmVudElkIjogMTQsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzNiwNCiAgICAibmFtZSI6ICJMT05HIE5FQ0svTEFUQVMiLA0KICAgICJwYXJlbnRJZCI6IDE1LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogMzcsDQogICAgIm5hbWUiOiAiQ0hPUFAiLA0KICAgICJwYXJlbnRJZCI6IDE1LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogMzgsDQogICAgIm5hbWUiOiAiQ0FJUElSSU5IQSIsDQogICAgInBhcmVudElkIjogMTYsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiAzOSwNCiAgICAibmFtZSI6ICJHSU4iLA0KICAgICJwYXJlbnRJZCI6IDE2LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogNDAsDQogICAgIm5hbWUiOiAiUE9Sw4dPRVMiLA0KICAgICJwYXJlbnRJZCI6IDEsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiA0MSwNCiAgICAibmFtZSI6ICJIQU1CVUdFUlMiLA0KICAgICJwYXJlbnRJZCI6IDMsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiA0MiwNCiAgICAibmFtZSI6ICJLSURTIiwNCiAgICAicGFyZW50SWQiOiA3LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogNDMsDQogICAgIm5hbWUiOiAiR1VBUk5Jw4fDg08iLA0KICAgICJwYXJlbnRJZCI6IDcsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiA0NCwNCiAgICAibmFtZSI6ICJFU1BFVE8gRE9DRSIsDQogICAgInBhcmVudElkIjogMTIsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiA0NSwNCiAgICAibmFtZSI6ICJCVUZGRVQiLA0KICAgICJwYXJlbnRJZCI6IDcsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0sDQogIHsNCiAgICAiaWQiOiA0NiwNCiAgICAibmFtZSI6ICJTQUxBREFTIiwNCiAgICAicGFyZW50SWQiOiA3LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogNDcsDQogICAgIm5hbWUiOiAiRVhFQ1VUSVZPIiwNCiAgICAicGFyZW50SWQiOiA3LA0KICAgICJ2aXNpYmxlIjogdHJ1ZQ0KICB9LA0KICB7DQogICAgImlkIjogNDgsDQogICAgIm5hbWUiOiAiRE9DRVMgQ0FJWEEiLA0KICAgICJwYXJlbnRJZCI6IDAsDQogICAgInZpc2libGUiOiB0cnVlDQogIH0NCl0=[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemFamily[NP]SIZE[EQ]0[NP]TOTALSIZE[EQ]0[NP]PART[EQ]0[NP]LIMIT[EQ]0[NP]SYNCVERSION[EQ]0[NP]MESSAGETYPE[EQ]XDPeople.Entities.PostDataListMessage[NP]MESSAGEID[EQ]29d94973-6b8e-4803-9223-725bbc00f6d7[NP]TERMINALID[EQ]1[EOM]
```

**Decrypted**
```json
[
 {
   "id": 1,
   "name": "ENTRADAS",
   "parentId": 0,
   "visible": true
 },
 {
   "id": 3,
   "name": "CORTES PARRILLERO",
   "parentId": 0,
   "visible": true 
 },
 ...
]
```

#### Exemplo 2 - Tabela de Relação de Produtos e Complementos

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemComplement[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]e6791a88-6e74-4354-bd80-196390847b79[EOM]
```

**Decrypted**

```json
[
 {
   "itemId": "100",
   "complementId": "103",
   "type": 0,
   "quantity": 0.0
 },
 {
   "itemId": "100",
   "complementId": "105",
   "type": 0,
   "quantity": 0.0
 },
 ...
]
```

#### Exemplo 3 - Relação de Famílias de Complementos

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemFamilyComplement[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]505cbf8b-3515-4bf2-abab-5cd6ab260d3d[EOM]
```

**Response**
```
POSTDATALIST[NP]OBJECT[EQ]W10=[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemFamilyComplement[NP]SIZE[EQ]0[NP]TOTALSIZE[EQ]0[NP]PART[EQ]0[NP]LIMIT[EQ]0[NP]SYNCVERSION[EQ]0[NP]MESSAGETYPE[EQ]XDPeople.Entities.PostDataListMessage[NP]MESSAGEID[EQ]b69bcd5f-3aed-4fc8-a8a3-1aa2668627bd[NP]TERMINALID[EQ]1[EOM]
```

##### Exemplo 4 - Código de Barras

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemBarcode[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]8752e28d-ce7c-4ec8-ac69-65f09a834297[EOM]
```

**Response**
```
POSTDATALIST[NP]OBJECT[EQ]Ww0KICB7DQogICAgIml0ZW1JZCI6ICI0IiwNCiAgICAiYmFyQ29kZSI6ICIyMzciLA0KICAgICJxdWFudGl0eSI6IDEuMCwNCiAgICAicHJpY2UiOiAzOC4wLA0KICAgICJ0eXBlIjogMCwNCiAgICAiYXR0cmlidXRlcyI6IG51bGwNCiAgfSwNCiAgew0KICAgICJpdGVtSWQiOiAiMDAxMjA4IiwNCiAgICAiYmFyQ29kZSI6ICI3ODk4OTA5Njg1MzY2IiwNCiAgICAicXVhbnRpdHkiOiAxLjAsDQogICAgInByaWNlIjogMC4wLA0KICAgICJ0eXBlIjogMCwNCiAgICAiYXR0cmlidXRlcyI6IG51bGwNCiAgfSwNCiAgew0KICAgICJpdGVtSWQiOiAiMDAwMzk4IiwNCiAgICAiYmFyQ29kZSI6ICI3ODk4OTY1MDI4MDIyIiwNCiAgICAicXVhbnRpdHkiOiAxLjAsDQogICAgInByaWNlIjogMC4wLA0KICAgICJ0eXBlIjogMCwNCiAgICAiYXR0cmlidXRlcyI6IG51bGwNCiAgfSwNCiAgew0KICAgICJpdGVtSWQiOiAiMDAxMDMzIiwNCiAgICAiYmFyQ29kZSI6ICI3ODk4OTY1MDI4MDQ2IiwNCiAgICAicXVhbnRpdHkiOiAxLjAsDQogICAgInByaWNlIjogMC4wLA0KICAgICJ0eXBlIjogMCwNCiAgICAiYXR0cmlidXRlcyI6IG51bGwNCiAgfSwNCiAgew0KICAgICJpdGVtSWQiOiAiMDAwNDA2IiwNCiAgICAiYmFyQ29kZSI6ICI3ODk4OTY1MDI4MDUzIiwNCiAgICAicXVhbnRpdHkiOiAxLjAsDQogICAgInByaWNlIjogMC4wLA0KICAgICJ0eXBlIjogMCwNCiAgICAiYXR0cmlidXRlcyI6IG51bGwNCiAgfSwNCiAgew0KICAgICJpdGVtSWQiOiAiMDAwNDA3IiwNCiAgICAiYmFyQ29kZSI6ICI3ODk4OTY1MDI4MDYwIiwNCiAgICAicXVhbnRpdHkiOiAxLjAsDQogICAgInByaWNlIjogMC4wLA0KICAgICJ0eXBlIjogMCwNCiAgICAiYXR0cmlidXRlcyI6IG51bGwNCiAgfSwNCiAgew0KICAgICJpdGVtSWQiOiAiMTIxMSIsDQogICAgImJhckNvZGUiOiAiNzg5MTIzNTkiLA0KICAgICJxdWFudGl0eSI6IDEuMCwNCiAgICAicHJpY2UiOiAzLjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9LA0KICB7DQogICAgIml0ZW1JZCI6ICIwMDAzOTgiLA0KICAgICJiYXJDb2RlIjogIjc4OTg5NjUwMjgwMjIiLA0KICAgICJxdWFudGl0eSI6IDAuMCwNCiAgICAicHJpY2UiOiAwLjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9LA0KICB7DQogICAgIml0ZW1JZCI6ICIwMDA0MDYiLA0KICAgICJiYXJDb2RlIjogIjc4OTg5NjUwMjgwNTMiLA0KICAgICJxdWFudGl0eSI6IDAuMCwNCiAgICAicHJpY2UiOiAwLjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9LA0KICB7DQogICAgIml0ZW1JZCI6ICIwMDA0MDciLA0KICAgICJiYXJDb2RlIjogIjc4OTg5NjUwMjgwNjAiLA0KICAgICJxdWFudGl0eSI6IDAuMCwNCiAgICAicHJpY2UiOiAwLjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9LA0KICB7DQogICAgIml0ZW1JZCI6ICIwMDEwMzMiLA0KICAgICJiYXJDb2RlIjogIjc4OTg5NjUwMjgwNDYiLA0KICAgICJxdWFudGl0eSI6IDAuMCwNCiAgICAicHJpY2UiOiAwLjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9LA0KICB7DQogICAgIml0ZW1JZCI6ICIwMDEyMDgiLA0KICAgICJiYXJDb2RlIjogIjc4OTg5MDk2ODUzNjYiLA0KICAgICJxdWFudGl0eSI6IDAuMCwNCiAgICAicHJpY2UiOiAwLjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9LA0KICB7DQogICAgIml0ZW1JZCI6ICIxMjExIiwNCiAgICAiYmFyQ29kZSI6ICI3ODkxMjM1OSIsDQogICAgInF1YW50aXR5IjogMC4wLA0KICAgICJwcmljZSI6IDMuMCwNCiAgICAidHlwZSI6IDAsDQogICAgImF0dHJpYnV0ZXMiOiBudWxsDQogIH0sDQogIHsNCiAgICAiaXRlbUlkIjogIjQiLA0KICAgICJiYXJDb2RlIjogIjIzNyIsDQogICAgInF1YW50aXR5IjogMC4wLA0KICAgICJwcmljZSI6IDM4LjAsDQogICAgInR5cGUiOiAwLA0KICAgICJhdHRyaWJ1dGVzIjogbnVsbA0KICB9DQpd[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileItemBarcode[NP]SIZE[EQ]0[NP]TOTALSIZE[EQ]0[NP]PART[EQ]0[NP]LIMIT[EQ]0[NP]SYNCVERSION[EQ]0[NP]MESSAGETYPE[EQ]XDPeople.Entities.PostDataListMessage[NP]MESSAGEID[EQ]d08c97e9-e942-491c-9d3f-bbaf11b6d5b2[NP]TERMINALID[EQ]1[EOM]
```

**Decrypted**

```json
[
 {
   "itemId": "4",
   "barcode": "237",
   "quantity": 1.0,
   "price": 38.0,
   "type": 0,
   "attributes": null
 },
 {
   "itemId": "100308",
   "barcode": "7898965028022",
   "quantity": 1.0,
   "price": 0.0,
   "type": 0,
   "attributes": null
 },
 ...
]
```

#### Exemplo 5 - Composição do Cardápio

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileMenuComposition[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]3293beda-e440-4c68-a52b-fa6d34134ca4[EOM]
```

**Response**
```
POSTDATALIST[NP]OBJECT[EQ]W10=[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileMenuComposition[NP]SIZE[EQ]0[NP]TOTALSIZE[EQ]0[NP]PART[EQ]0[NP]LIMIT[EQ]0[NP]SYNCVERSION[EQ]0[NP]MESSAGETYPE[EQ]XDPeople.Entities.PostDataListMessage[NP]MESSAGEID[EQ]12b81b83-c8f0-4b35-ac69-bce3de1b3d12[NP]TERMINALID[EQ]1[EOM]
```

Um padrão interessante, é que quando é realizada uma requisição de dados, e não há nenhum dado para ser retornado, é retornado um objeto vazio.

#### Exemplo 6 - Visualização de Mesas por Zonas

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileBoard[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]e7c7e937-2680-4270-916b-b09eec6fab52[EOM]
```

**Decrypted**

```json
[
 {
   "id": 1,
   "name": "1",
   "zoneId": 1
 },
 {
   "id": 2,
   "name": "2",
   "zoneId": 1
 },
 ...
]
```

#### Exemplo 7 - Visualização de Mesas por Zonas

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileBoardZone[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]16850abe-191a-4509-9e04-9744a869fa05[EOM]
```

**Response**
```json
[
 {
   "id": 1,
   "name": "BISTRO RUA",
   "authorizedEmployees": ""
 },
 {
   "id": 2,
   "name": "VARANDA ",
   "authorizedEmployees": ""
 },
 ...
]
```

#### Exemplo 8 - Visualização de Status de Mesas

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileBoardStatus[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]9292c6fb-ed9a-451d-8ec2-5bdceadf03d3[EOM]
```

**Response**
```json
[
 {
   "id": 1,
   "name": "1",
   "status": 0,
   "lockDescription": null,
   "inactive": false,
   "freeTable": false,
   "initialUser": 0
 },
 {
   "id": 2,
   "name": "2",
   "status": 2,
   "lockDescription": null,
   "inactive": false,
   "freeTable": false,
   "initialUser": 5
 },
  ...
]
```

#### Exemplo 9 - Visualização de Tipos de Pagamento

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobilePaymentType[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]9561f840-4d3a-4700-857a-d2f03cda0579[EOM]
```

**Response**
```json
[
 {
   "id": 1,
   "name": "Dinheiro",
   "paymentMechanism": "NU",
   "sendToCheckingAccount": false
 },
 {
   "id": 3,
   "name": "Debito",
   "paymentMechanism": "CD",
   "sendToCheckingAccount": false
 },
 {
   "id": 4,
   "name": "Credito",
   "paymentMechanism": "CC",
   "sendToCheckingAccount": false
 }
]
```

#### Exemplo 10 - Configurações do Servidor Móvel

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileServerSettings[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]53f2b0d0-ff21-402c-aeb4-4abf719a0303[EOM]
```

#### Exemplo 11 - Usuários Móveis

**Request**
```
GETDATALIST[NP]PROTOCOLVERSION[EQ]1[NP]OBJECTTYPE[EQ]XDPeople.Entities.MobileUser[NP]PART[EQ]0[NP]LIMIT[EQ]5000[NP]USERID[EQ]0[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.GetDataListMessage[NP]MESSAGEID[EQ]e1230410-d648-42cf-9fb8-98f01c7be383[EOM]
```

**Response**
```json
[
 {
   "id": 1,
   "name": "FERNANDO",
   "password": "35172e3e25d3c9373e8970ea0660999a7bd9dd83cce5a9eb7fed7fcf12463a95",
   "mobilePhone": null,
   "phone": null,
   "email": null,
   "image": ..., // Imagem em base64
   "isSupervisor": true,
   "canVoidOrders": true,
   "canCloseAccount": true,
   "canTransfer": true,
   "canMakeDiscounts": true,
   "canMakePartialPayments": true,
   "canChangeSettings": true
 },
  ...
]
```

#### Exemplo 12 

**Request**
```
POSTQUEUE[NP]PROTOCOLVERSION[EQ]2[NP]QUEUE[EQ]eyJhcHBWZXJzaW9uIjowLCJlbXBsb3llZUlkIjoxLCJndWlkIjoiYzE1MTkzMDUtMmRmYi00OTI2
LWFhM2YtNThjZjQ3ZTIxOTM0IiwiaWQiOjgsIm9yZGVycyI6W10sInBlcnNvbnNOdW1iZXIiOjAs
InN0YXR1cyI6MSwidGFibGUiOjQxLCJ0aW1lIjoxNzI3OTgxNzMzODQzLCJBY3Rpb24iOjN9
[NP]TOKEN[EQ]88e90ba5d746ebf29e968500c10fcf74e155d799[NP]MESSAGETYPE[EQ]XDPeople.Entities.PostActionMessage[NP]MESSAGEID[EQ]49a15870-a0aa-4d32-80b9-8b55f659021f[EOM]
```

**Queue**
```json
{"appVersion":0,"employeeId":1,"guid":"c1519305-2dfb-4926-aa3f-58cf47e21934","id":8,"orders":[],"personsNumber":0,"status":1,"table":41,"time":1727981733843,"Action":3}
```

**Response**
```
QUEUESYNCSUCCESS[NP]SYNCVERSION[EQ]0[NP]MESSAGES[EQ]W10=[EOM]
```


### Conclusão

