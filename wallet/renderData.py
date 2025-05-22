
from decimal import Decimal
import os
from central_events.models import Events
from insb_port import settings
from port.models import Chapters_Society_and_Affinity_Groups, Panels
from wallet.models import Wallet, WalletEntry, WalletEntryFile, WalletEventStatus


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

        wallet = Wallet.objects.get(sc_ag=sc_ag)
        if wallet_entry.entry_type == 'CASH_IN':
            wallet.balance += Decimal(wallet_entry.amount)
        elif wallet_entry.entry_type == 'CASH_OUT':
            wallet.balance -= Decimal(wallet_entry.amount)
        wallet.save()
        
        for file in entry_files:
            WalletEntryFile.objects.create(wallet_entry=wallet_entry, document=file)

        if event_id:
            if not WalletEventStatus.objects.filter(wallet_event=event).exists():
                WalletEventStatus.objects.create(wallet_event=event)

    def update_wallet_entry(entry_id, entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files):

        categories = str(entry_categories).split(',')

        wallet_entry = WalletEntry.objects.get(id=entry_id)
        wallet_entry.entry_date_time = entry_date_time
        wallet_entry.name = name
        wallet_entry.contact = contact
        wallet_entry.remarks = entry_remark
        wallet_entry.payment_mode = payment_mode

        if wallet_entry.amount != Decimal(entry_amount):
            wallet = Wallet.objects.get(sc_ag=wallet_entry.sc_ag)
            if wallet_entry.entry_type == 'CASH_IN':
                wallet.balance -= Decimal(wallet_entry.amount)
                wallet_entry.amount = entry_amount
                wallet.balance += Decimal(wallet_entry.amount)
            elif wallet_entry.entry_type == 'CASH_OUT':
                wallet.balance += Decimal(wallet_entry.amount)
                wallet_entry.amount = entry_amount
                wallet.balance -= Decimal(wallet_entry.amount)

            wallet.save()

        wallet_entry.save()
        wallet_entry.categories.add(*categories)

        for file in entry_files:
            WalletEntryFile.objects.create(wallet_entry=wallet_entry, document=file)

    def delete_wallet_entry(entry_id):

        wallet_entry = WalletEntry.objects.get(id=entry_id)
        wallet_entry_files = WalletEntryFile.objects.filter(wallet_entry=wallet_entry)
        
        for file in wallet_entry_files:
            path = settings.MEDIA_ROOT+str(file.document)
            if os.path.exists(path):
                os.remove(path)
            file.delete()

        wallet_event_status = WalletEventStatus.objects.filter(wallet_event=wallet_entry.entry_event)
        if wallet_event_status.exists():
            wallet_event_status.delete()

        wallet = Wallet.objects.get(sc_ag=wallet_entry.sc_ag)
        if wallet_entry.entry_type == 'CASH_IN':
            wallet.balance -= Decimal(wallet_entry.amount)
        elif wallet_entry.entry_type == 'CASH_OUT':
            wallet.balance += Decimal(wallet_entry.amount)

        wallet.save()
        wallet_entry.delete()

    def delete_entry_file(file_id):

        entry_file = WalletEntryFile.objects.get(id=file_id)
        
        path = settings.MEDIA_ROOT+str(entry_file.document)
        if os.path.exists(path):
            os.remove(path)
        entry_file.delete()
