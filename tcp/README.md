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

### Conclusão

