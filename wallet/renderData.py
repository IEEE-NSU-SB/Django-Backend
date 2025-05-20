
from central_events.models import Events
from port.models import Chapters_Society_and_Affinity_Groups, Panels
from wallet.models import WalletEntry, WalletEntryFile, WalletEventStatus


class WalletManager:

    def add_wallet_entry(primary, entry_type, entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files, event_id):
        
        sc_ag = Chapters_Society_and_Affinity_Groups.objects.filter(primary=primary).values('id')[0]['id']

        categories = str(entry_categories).split(',')

        event = None
        if event_id:
            event = Events.objects.get(id=event_id)

        wallet_entry = WalletEntry.objects.create(
                                   entry_date_time=entry_date_time,
                                   amount=entry_amount,
                                   name=name,
                                   contact=contact,
                                   remarks=entry_remark,
                                   payment_mode=payment_mode,
                                   entry_type=entry_type,
                                   entry_event=event,
                                   sc_ag_id=sc_ag,
                                   tenure=Panels.objects.get(panel_of=sc_ag, current=True))
        
        wallet_entry.categories.add(*categories)
        
        for file in entry_files:
            WalletEntryFile.objects.create(wallet_entry=wallet_entry, document=file)

        if event_id:
            if not WalletEventStatus.objects.exists(wallet_event=event):
                WalletEventStatus.objects.create(wallet_event=event)