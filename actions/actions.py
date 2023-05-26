import datetime
from typing import Text, List, Any, Dict, Optional
from datetime import date, timedelta
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted, AllSlotsReset
import pymongo
global SiPaga
global NoPaga
global motivo
global tipo_contacto
global compromiso_p
global derivacion
global fecha_com
global entrega_info



CONNECTION_STRING = "mongodb://172.16.1.41:27017,172.16.1.42:27017,172.16.1.43:27017/?replicaSet=haddacloud-rs&readPreference=secondaryPreferred"
# CONNECTION_STRING = "mongodb://Admin:T3c4dmin1.@172.16.1.228:27017/data_warehouse?authSource=admin&readPreference=secondaryPreferred"
myclient = pymongo.MongoClient(CONNECTION_STRING)

organization_id=21

class SetNameAction(Action):
    def name(self):
        return "set_name_action"

    def run(self, dispatcher, tracker, domain):
        #tracker.update(Restarted())
        try:
            splits = tracker.sender_id
            customer_id,campaign_group,caller_id,phone_number = splits.split('|')
            names = getNameByCustomerID(customer_id,organization_id)
            print(names)
        except:
            names = "Jose Miguel"
        try: 
            deuda_mora, fecha_vcto = getDebtsByCustomerID(customer_id, campaign_group)
        except:
            deuda_mora = "10000"
            fecha_vcto = "01-01-1979"
        try:
            valueContesta = "si"
            value_to_set = "si"
            update_key_for_customer(customer_id, campaign_group, caller_id, valueContesta, value_to_set, names, phone_number, deuda_mora)
        except Exception as e:
            print("No se pudo actualizar el estado de corte")
            print(f"Error: {e}")
        print(f"deuda_mora : {deuda_mora}")
        print(f"fecha_vcto : {fecha_vcto}")
        print(f"phone_number : {phone_number}")
        return [SlotSet("name", names),SlotSet("fecha_vcto", fecha_vcto), SlotSet("monto", deuda_mora),SlotSet("phone_number", phone_number)]



def getNameByCustomerID(customer_id,organization_id):

    mydb = myclient["haddacloud-v2"]
    mycol = mydb["deudors"]

    x = mycol.find_one({ 'organization_id': int(organization_id), 'customer_id': str(customer_id)  })

    return x["nombre"]

def getDebtsByCustomerID(customer_id, campaign_group):

    mydb = myclient["haddacloud-v2"]
    mycol = mydb["debts"]

    x = mycol.find_one({  'organization_id': int(organization_id), 'customer_id': str(customer_id), 'group_campaign_id': int(campaign_group)  }, sort=[('updated_at', -1)])
 
    return x["deuda_total"], x["fecha_vcto"]

def update_key_for_customer(customer_id, campaign_group, caller_id, valueContesta, value_to_set, names, phone_number, deuda_mora):
    mydb = myclient["haddacloud-v2"]
    mycol = mydb["voicebot-interactions"]

    result = mycol.update_one(
        {
            "customer_id": str(customer_id),
            "organization_id": int(organization_id),
            "group_campaign_id": int(campaign_group),
            "caller_id": str(caller_id)
        },
        {
            "$set": {
                "flujo": "hites_derivacion",
                "contesta": valueContesta,
                "corta": value_to_set,
                "derivado_o_no": None,
                "es_persona_correcta": None,
                "conoce_o_no": None,
                "opcion_pago": None,
                "paga_o_no": None,
                "name": names.lower(),
                "monto": None,
                "fecha_vcto": None,
                "fecha_pago": None,
                "phone_number": phone_number,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now()
            }
        },
        upsert=True
    )

    print(f"Documentos modificados: {result.modified_count}")

# Luego puedes llamar a la función de esta manera


def month_converter(i):
       month = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
       return month[i-1]


        
    
class ActionSiPaga(Action):
    def name(self):
        return "action_si_paga"

    def run(self, dispatcher, tracker, domain):
        
        today_date = date.today()
        td = timedelta(3)
        fechaPago=str(today_date + td)
        print("Fecha de Pago: ",fechaPago)
        return [SlotSet("fecha_pago", fechaPago)]



class ActionRestart2(Action):
    """Resets the tracker to its initial state.
    Utters the restart template if available."""

    def name(self) -> Text:
        return "action_restart2"

    async def run(self, dispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [Restarted()]

class ActionSlotReset(Action):
    def name(self):
        return 'action_slot_reset'
    def run(self, dispatcher, tracker, domain):
        return[AllSlotsReset()]


class ActionGuardarConoce(Action):

    def name(self) -> Text:
        return "action_guardar_conoce_o_no"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        conoce_o_no = tracker.get_slot("conoce_o_no")

        if isinstance(conoce_o_no, list):
            conoce_o_no = conoce_o_no[0]


        if tracker.get_slot("conoce_o_no") is None:
            print("Es None ..")
        print("conoce_o_no: ", conoce_o_no)
            #dispatcher.utter_message(text=f"Razón: {Razón}")
        return []


class ActionRecibirEsoNo(Action):

    def name(self) -> Text:
        return "action_recibir_es_o_no"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        es_o_no = tracker.get_slot("es_o_no")
        if isinstance(es_o_no, list):
            es_o_no = es_o_no[0]

        print("es_o_no: ", es_o_no)
            #dispatcher.utter_message(text=f"Razón: {Razón}")
        return []


conoce_intent=None
class ActionConoceONo(Action):
    def name(self):
        return "action_save_conoce_o_no"

    def run(self, dispatcher, tracker, domain):
        global conoce_intent
        # Obtener la intención actual
        latest_message = tracker.latest_message
        conoce_intent = latest_message['intent']['name']
        if isinstance(conoce_intent, list):
            conoce_intent = conoce_intent[0]
        print(f'conoce o no: {conoce_intent}')


paga_intent=None
class ActionPagaONo(Action):
    def name(self):
        return "action_save_intent_paga_o_no"

    def run(self, dispatcher, tracker, domain):
        global paga_intent
        # Obtener la intención actual
        latest_message = tracker.latest_message
        paga_intent = latest_message['intent']['name']

        if isinstance(paga_intent, list):
            paga_intent = paga_intent[0]

        print(f'paga_intent : {paga_intent}')

es_o_no_intent=None
class ActionConoceONo(Action):
    def name(self):
        return "action_es_o_no"

    def run(self, dispatcher, tracker, domain):
        global es_o_no_intent
        # Obtener la intención actual
        latest_message = tracker.latest_message
        es_o_no_intent = latest_message['intent']['name']
    
        if isinstance(es_o_no_intent, list):
            es_o_no_intent = es_o_no_intent[0]
        print(f'es_o_no_intent: {es_o_no_intent}')


class ActionSiPaga(Action):
    def name(self):
        return "action_save_data"

    def run(self, dispatcher, tracker, domain):
        mydb = myclient["haddacloud-v2"]
        mycol = mydb["voicebot-interactions"]


        splits = tracker.sender_id
        customer_id,campaign_group,caller_id,phone_number = splits.split('|')
        print("-------------------------------------------------------------")
        print(tracker.slots)

        # Obtener la intención actual
        latest_message = tracker.latest_message
        current_intent = latest_message['intent']['name']
        
        # Imprimir el nombre de la intención
        print(f'current_intent: {current_intent}')
        print(f'current_intent: {type(current_intent)}')
        if(current_intent=="afirmación"):
            current_intent="Si"
        elif(current_intent=="negación"):
            current_intent="No"
        else:
           current_intent = None

        slots_to_update = [
            "name",
            "derivado_o_no",
            "es_persona_correcta",
            "conoce_o_no",
            "fecha_vcto",
            "fecha_pago",
            "monto",
            "paga_o_no",
            "opcion_pago",
            "phone_number"
        ]
        
        slots_to_lower = [
            "name",
            "derivado_o_no",
            "es_persona_correcta",
            "conoce_o_no",
            "paga_o_no",
            "opcion_pago",
            
        ]
        
        updated_slots = {slot: (tracker.slots.get(slot).lower() if tracker.slots.get(slot) else None) 
                         if slot in slots_to_lower 
                         else tracker.slots.get(slot) or None 
                         for slot in slots_to_update}


        print(f'name: {updated_slots["name"]}')
        print(f'es_persona_correcta: {updated_slots["es_persona_correcta"]}')
        print(f'conoce_o_no: {updated_slots["conoce_o_no"]}')
        print(f'fecha_vcto: {updated_slots["fecha_vcto"]}')
        print(f'monto: {updated_slots["monto"]}')
        print(f'paga_o_no: {updated_slots["paga_o_no"]}')
        print(f'opcion_pago: {current_intent}')
        print(f'phone_number: {updated_slots["phone_number"]}')
        print(f'fecha_pago: {updated_slots["fecha_pago"]}')
        


        print("-------------------------------------------------------------")

        result = mycol.update_one(
        {
            "customer_id": str(customer_id),
            "organization_id": int(organization_id),
            "group_campaign_id": int(campaign_group),
            "caller_id": str(caller_id)
        },
        {
            "$set": {
                "name": "hites_derivacion",
                "contesta":"si",
                "corta": "no",
                "derivado_o_no":current_intent.lower(),
                "es_persona_correcta": updated_slots["es_persona_correcta"],
                "conoce_o_no": updated_slots["conoce_o_no"],
                "opcion_pago": None,
                "paga_o_no": None,
                "name": updated_slots["name"],
                "monto": None,
                "fecha_vcto": None,
                "fecha_pago": None,
                "phone_number": updated_slots["phone_number"],
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now()
            }
        },
        upsert=True
        )
       
        print(f'result: {result}')
        # print(f'{result.modified_count} Updateds')
        name=None
        es_persona_correcta=None
        conoce_o_no=None
        fecha_vcto=None
        fecha_pago=None
        monto=None
        paga_o_no=None
        fecha_vcto=None
        opcion_pago=None
        phone_number=None

        return []
    

class ActionSlotReset(Action):  
    def name(self):         
        return 'action_slot_reset'  
    def run(self, dispatcher, tracker, domain):
        return[AllSlotsReset()]



class ActionRepeatLastQuestion(Action):

    def name(self) -> Text:
        return "action_repeat_last_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        last_bot_utterance = None

        for event in reversed(tracker.events):
            if event.get("event") == "bot":
                last_bot_utterance = event.get("text")
                break

        if last_bot_utterance:
            dispatcher.utter_message(text=last_bot_utterance)
        else:
            dispatcher.utter_message(text="Lo siento, no tengo información sobre la última pregunta.")

        return []

class ActionFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Obtener la intención predicha
        predicted_intent = tracker.latest_message['intent']['name']

        # Establecer la ranura 'predicted_intent' con la intención predicha
        return [SlotSet("predicted_intent", predicted_intent)]