
from port.models import Chapters_Society_and_Affinity_Groups, Panels
from wallet.models import WalletEntry, WalletEntryFile


class WalletManager:

    def add_wallet_entry(primary, entry_type, entry_date_time, entry_amount, name, contact, entry_remark, payment_mode, entry_categories, entry_files):
        
        sc_ag = Chapters_Society_and_Affinity_Groups.objects.get(primary=primary)

        categories = str(entry_categories).split(',')

        wallet_entry = WalletEntry.objects.create(entry_date_time=entry_date_time,
                                   amount=entry_amount,
                                   name=name,
                                   contact=contact,
                                   remarks=entry_remark,
                                   payment_mode=payment_mode,
                                   entry_type=entry_type,
                                   sc_ag=sc_ag,
                                   tenure=Panels.objects.get(panel_of=sc_ag, current=True))
        
        wallet_entry.categories.add(*categories)
        
        for file in entry_files:
            WalletEntryFile.objects.create(wallet_entry=wallet_entry, document=file)