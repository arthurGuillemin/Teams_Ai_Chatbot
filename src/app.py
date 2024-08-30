from http import HTTPStatus
from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware
import aiohttp
from botbuilder.core import TurnContext, BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity, ConversationAccount
from config import Config

routes = web.RouteTableDef()

@routes.post("/api/messages")
async def on_messages(req: web.Request) -> web.Response:
    try:
        request_json = await req.json()
        user_message = request_json.get('text')
        print("Received message:", user_message)
        
        # Effectuer un appel HTTP asynchrone avec aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://langchaincontainer--xmbw6s7.mangocliff-ea893619.francecentral.azurecontainerapps.io/rag-mongo/invoke",
                json={'input': user_message}
            ) as response:
                if response.status != 200:
                    print(f"Error response from rag-mongo service: {response.status}")
                    return web.json_response({'error': 'Error from rag-mongo service'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                
                response_data = await response.json()
                full_response = response_data['output']
                print("Response from rag-mongo service:", full_response)
                
                settings = BotFrameworkAdapterSettings(app_id="", app_password="")
                adapter = BotFrameworkAdapter(settings)
                conversation_id = request_json.get('conversation', {}).get('id')
                activity = Activity(
                    type="message",
                    text=full_response,
                    service_url=request_json.get('serviceUrl'),
                    conversation=ConversationAccount(id=conversation_id)
                )
                
                connector_client = await adapter.create_connector_client(activity.service_url)
                await connector_client.conversations.send_to_conversation(activity.conversation.id, activity)
                
        return web.json_response({'response': full_response})
    except Exception as e:
        print("Exception occurred:", str(e))
        return web.json_response({'error': str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

app = web.Application(middlewares=[aiohttp_error_middleware])
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=Config.PORT)
