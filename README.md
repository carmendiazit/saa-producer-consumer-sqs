# Producer-Consumer Pattern using AWS Lambda, SQS and DynamoDB with SAM

Aplicación SAM - SimuLearn Lab  
**Patrón:** Producer Lambda → SQS → Consumer Lambda → DynamoDB

## Prerrequisitos

Para ejecutar este proyecto necesitás lo siguiente:

**1. Cuenta de AWS con capa gratuita (AWS Free Tier)**  
Los servicios utilizados en este proyecto (Lambda, SQS y DynamoDB) forman parte de la capa gratuita permanente de AWS (*Always Free*), lo que significa que no tienen fecha de vencimiento y están disponibles para todas las cuentas:
- **AWS Lambda**: 1 millón de invocaciones y 400.000 GB-segundos por mes
- **Amazon SQS**: 1 millón de solicitudes por mes
- **Amazon DynamoDB**: 25 GB de almacenamiento y 200 millones de solicitudes por mes

Este lab no genera costo si se mantiene dentro de esos límites. Se recomienda eliminar el stack al finalizar con `sam delete`.  
Más información: https://aws.amazon.com/free/

**2. Credenciales de AWS configuradas**  
El AWS CLI debe tener un perfil configurado con las credenciales de tu cuenta (Access Key ID y Secret Access Key) y la región por defecto. Podés verificarlo con:
```bash
aws configure list
aws sts get-caller-identity
```
Más información: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html

**3. Python 3.13**  
Requerido localmente para el build de SAM. Descarga: https://www.python.org/downloads/

**4. AWS CLI**  
Interfaz de línea de comandos para interactuar con los servicios AWS.  
Instalación: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

**5. AWS SAM CLI**  
Herramienta para construir y desplegar aplicaciones serverless.  
Instalación: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

---

## Arquitectura

```
[ProducerFunction]
       │
       ▼  MessageBody (JSON)
[MyMessageQueue]  ──(maxReceiveCount=3)──► [MyMessageQueueDLQ]
       │
       ▼  SQS Trigger (batch=10)
[ConsumerFunction]
       │
       ▼
[checkinData DynamoDB]
```

## Estructura del proyecto

```
saa-producer-consumer-sqs/
├── template.yaml          # Infraestructura SAM (IaC)
├── samconfig.toml         # Configuración de deploy
├── .gitignore
├── events/
│   └── sqs-event.json     # Evento de prueba local
└── src/
    ├── producer/
    │   └── app.py         # Lambda que publica en SQS
    └── consumer/
        └── app.py         # Lambda que lee SQS y escribe en DynamoDB
```

## Comandos

### Build
```bash
sam build
```

### Test local - Consumer (requiere Docker)
```bash
sam local invoke ConsumerFunction --event events/sqs-event.json
```

### Deploy
```bash
sam deploy
```

> El `samconfig.toml` ya tiene todos los parámetros configurados. No es necesario `--guided`.

### Invocar Producer manualmente desde AWS CLI

El Producer acepta `coder_id`, `spot_id` y `timestamp` desde el evento. Si no se pasan, usa valores default (`123`, `321`, timestamp actual).

```bash
aws lambda invoke \
  --function-name ProducerFunction \
  --region us-east-1 \
  --payload '{"coder_id": "456", "spot_id": "789"}' \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json
```

Sin parámetros (usa defaults):
```bash
aws lambda invoke \
  --function-name ProducerFunction \
  --region us-east-1 \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Ver logs en CloudWatch

```bash
sam logs --stack-name saa-producer-consumer-sqs --name ConsumerFunction --tail
sam logs --stack-name saa-producer-consumer-sqs --name ProducerFunction --tail
```

### Sondear la cola SQS

Primero obtenés el URL del Output del stack:
```bash
aws cloudformation describe-stacks \
  --stack-name saa-producer-consumer-sqs \
  --query "Stacks[0].Outputs" \
  --region us-east-1
```

Luego usás el valor de `QueueUrl`:
```bash
aws sqs receive-message \
  --queue-url <QueueUrl> \
  --max-number-of-messages 10 \
  --region us-east-1
```

Cantidad de mensajes sin consumir:
```bash
aws sqs get-queue-attributes \
  --queue-url <QueueUrl> \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --region us-east-1
```

### Ver mensajes en la DLQ

```bash
aws sqs receive-message \
  --queue-url <DLQUrl> \
  --max-number-of-messages 10 \
  --region us-east-1
```

### Consultar DynamoDB

```bash
aws dynamodb scan \
  --table-name checkinData \
  --region us-east-1
```

### Eliminar stack

```bash
sam delete --stack-name saa-producer-consumer-sqs --region us-east-1
```

## Modelo DynamoDB - checkinData

| Atributo   | Tipo | Rol           |
|------------|------|---------------|
| coderId    | S    | Partition Key |
| timestamp  | N    | Sort Key      |
| spotID     | S    | Atributo      |

## Notas

- El Producer usa la variable de entorno `QUEUE_URL` (inyectada por SAM desde `!Ref MyMessageQueue`)
- La DLQ captura mensajes que fallaron 3 veces (`maxReceiveCount: 3`)
- El Consumer usa `ReportBatchItemFailures` para procesar batches parciales sin perder mensajes válidos
- BillingMode DynamoDB: `PAY_PER_REQUEST` (on-demand, ideal para labs)
- Runtime: `python3.13`
- El flag `--cli-binary-format raw-in-base64-out` es requerido en Windows con Git Bash
