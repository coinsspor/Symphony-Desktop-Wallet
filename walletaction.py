import time
import tkinter as tk
import requests
from tkinter import ttk, messagebox
import mainscreen  # Ana ekran modülü
from delegate import delegate_to_validator  # delegate.py'den fonksiyonu import et
from transfer import transfer_token  # transfer.py'den transfer_token fonksiyonunu import et

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

valid_adr = None


def clear_content(root):
    for widget in root.winfo_children():
        widget.destroy()

def copy_to_clipboard(root, content):
    root.clipboard_clear()
    root.clipboard_append(content)
    root.update()
    messagebox.showinfo("Copy Success", f"{content} Copied!")

def fetch_balances(address):
    url = f"https://symphony-api.kleomedes.network/cosmos/bank/v1beta1/balances/{address}"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        data = response.json()
        return data.get('balances', [])
    else:
        print("Failed to fetch balances:", response.status_code)
        return []

def fetch_validators():
    url = "https://symphony-api.kleomedes.network/cosmos/staking/v1beta1/validators?pagination.limit=300&status=BOND_STATUS_BONDED"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        validators = response.json().get('validators', [])
        return [(v['description']['moniker'] + ' (' + f"{float(v['commission']['commission_rates']['rate']) * 100:.1f}%)", v['operator_address']) for v in validators]
    else:
        print("Failed to fetch validators:", response.status_code)
        return []

def format_balance(amount):
    # İlk olarak string'i float'a çevir, sonra sonucu formatla
    return f"{float(amount) / 10**6:.6f}"

def update_max_amount(entry, symhony_address, root):
    current_balances = fetch_balances(symhony_address)  # Her seferinde güncel bakiyeleri çek
    total_balance_wei = sum(int(balance['amount']) for balance in current_balances if balance['denom'] == 'note')
    total_balance_note = total_balance_wei / 1e6
    max_transferable_note = max(0, total_balance_note - 0.01)

    entry.delete(0, tk.END)
    if max_transferable_note > 0:
        entry.insert(0, f"{max_transferable_note:.6f}")
    else:
        entry.insert(0, "0.000000")
        messagebox.showinfo("Insufficient Balance", "You need at least 0.01 note more in your wallet to perform transactions.", parent=root)


def update_balance(balance_label, address):
    balances = fetch_balances(address)
    if balances:
        balance_str = " ".join([f"{format_balance(balance['amount'])} MLD" if balance['denom'] == 'note' else f"{format_balance(balance['amount'])} {balance['denom']}" for balance in balances])
        balance_label.config(text=f"Balances: {balance_str}")
    else:
        balance_label.config(text="Balances: 0")

def perform_transfer(entry, target_address_entry, fee_entry, gas_entry, symhony_address, private_key, root, balance_label):
    # Cüzdan adresi ve private key'in doğruluğunu kontrol edin
    #print(f"Transfer işlemi için kullanılan adres: {symhony_address}, Private Key: {private_key}")

    try:
        amount_note = float(entry.get())  # Kullanıcıdan alınan miktarı note cinsinden al
        amount_wei = int(amount_note * 10**6)  # Wei'ye çevir
    except ValueError:
        messagebox.showerror("Error", "Invalid amount entered. Please enter a numeric value.", parent=root)
        return

    # Güncel bakiyeleri çek
    current_balances = fetch_balances(symhony_address)
    total_balance_wei = sum(int(balance['amount']) for balance in current_balances if balance['denom'] == 'note')

    if amount_wei > total_balance_wei:
        messagebox.showwarning("Warning", "Insufficient funds for this transaction.", parent=root)
        return

    if total_balance_wei - amount_wei < 0.01 * 10**6:
        messagebox.showwarning("Warning", "Insufficient balance after transfer. Minimum balance of 0.01 note required.", parent=root)
        return

    # Tüm kontroller geçilirse, transfer işlemini doğru sıra ile parametreleri vererek gerçekleştir
    success = transfer_token(target_address_entry.get(), str(amount_wei), 'note', fee_entry.get(), gas_entry.get(), private_key)
    print("sonuc",success)
    if success==True:
        time.sleep(5)
        update_balance(balance_label, symhony_address)


def perform_delegate(valid_adr, entry, gas_entry, fee_entry, symhony_address, private_key, root,balance_label):
    try:
        amount_note = float(entry.get())  # Kullanıcıdan alınan miktarı note cinsinden al
        amount_wei = int(amount_note * 10**6)  # Wei'ye çevir
    except ValueError:
        messagebox.showerror("Error", "Invalid amount entered. Please enter a numeric value.", parent=root)
        return

    current_balances = fetch_balances(symhony_address)  # Güncel bakiyeleri çek
    total_balance_wei = sum(int(balance['amount']) for balance in current_balances if balance['denom']== 'note')

    if amount_wei > total_balance_wei:
        messagebox.showwarning("Warning", "Insufficient funds for this transaction.", parent=root)
        return

    if total_balance_wei - amount_wei < 0.01 * 10**6:
        messagebox.showwarning("Warning", "Insufficient balance after transfer. Minimum balance of 0.01 note required.", parent=root)
        return

    # Tüm kontroller geçilirse, transfer işlemini doğru sıra ile parametreleri vererek gerçekleştir
    success = delegate_to_validator(valid_adr, str(amount_wei), gas_entry.get(),fee_entry.get(),symhony_address,private_key)
    print("sonuc",success)
    if success==True:
        time.sleep(5)
        update_balance(balance_label, symhony_address)

def wallet_actions(root, symhony_address, private_key):
    clear_content(root)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background='#121B23')
    style.configure('TButton', background='#61cbf4', foreground='white', font=('Arial', 12))
    style.configure('TLabel', background='#121B23', foreground='white', font=('Arial', 12))
    style.configure('TEntry', fieldbackground='#D9EAF7', foreground='#000', font=('Arial', 12))
    style.configure('TCombobox', fieldbackground='#D9EAF7', foreground='#000', font=('Arial', 12))
    style.map('TCombobox', fieldbackground=[('readonly','#D9EAF7')])
    style = ttk.Style()
    style.configure('Small.TButton', font=('Helvetica', 8), padding=2)
    
    frame = ttk.Frame(root, style='TFrame')
    frame.pack(fill='both', expand=True)

    title_label = ttk.Label(frame, text="Wallet Information", font=('Arial', 20), background="#0e1018", foreground="white", anchor="center", padding=(0, 10))
    title_label.pack(fill='x')

    

    panel2 = ttk.Frame(frame, style='TFrame')
    panel2.pack(fill='x', pady=10)

    symp_frame = ttk.Frame(panel2, style='TFrame')
    symp_frame.pack(fill='x', pady=5)
    ttk.Label(symp_frame, text="Symphony Address:", font=('Arial', 12,'bold','underline'),foreground='orange').pack(side='left', padx=(10, 5))
    symp_label = ttk.Label(symp_frame, text=symhony_address, font=('Arial', 12, 'bold'))
    symp_label.pack(side='left')
    symp_copy_button = ttk.Button(symp_frame, text="Copy",style='Small.TButton', command=lambda: copy_to_clipboard(root, symhony_address))
    symp_copy_button.pack(side='left', padx=5)

    panel3 = ttk.Frame(frame, style='TFrame')
    panel3.pack(fill='both', expand=True, pady=(20, 10))

    tab_control = ttk.Notebook(frame, style='TNotebook')
    tab_transfer = ttk.Frame(tab_control, style='TFrame')
    tab_delegate = ttk.Frame(tab_control, style='TFrame')
    
    tab_control.add(tab_transfer, text='MLD Transfer')
    tab_control.add(tab_delegate, text='Delegate')
    


    
    validators = fetch_validators()
    setup_tab(tab_transfer, "Transfer", validators, symhony_address, private_key,root)
    setup_tab(tab_delegate, "Delegate", validators, symhony_address, private_key,root)
    
    
    global balance_label
    balance_label = ttk.Label(frame, text="Please click 'Update Balance' to view balance", style='TLabel')
    balance_label.pack(fill='x', pady=(10, 10))
    update_balance(balance_label, symhony_address)

    update_balance_button = ttk.Button(frame, text="Update Balance", command=lambda: update_balance(balance_label, symhony_address))
    update_balance_button.pack(fill='x', pady=(10, 10))
    tab_control.pack(expand=1, fill='both', pady=(0, 10))

    logout_button = ttk.Button(frame, text="Logout", command=lambda: mainscreen.show_main_screen(root))
    logout_button.pack(fill='x', pady=(10, 20))

def paste_to_entry(entry_widget, root):
    try:
        # Panodan içeriği al ve Entry widget'ına yapıştır
        content = root.clipboard_get()
        entry_widget.delete(0, tk.END)  # Mevcut içeriği temizle
        entry_widget.insert(0, content)  # Panodaki içeriği yapıştır
    except tk.TclError:
        print("Nothing to paste")



def setup_tab(tab, action_type, validators, symhony_address, private_key, root):
    if action_type == "Transfer":
        current_balances = fetch_balances(symhony_address)  # Mevcut bakiyeleri çek

        ttk.Label(tab, text='Target Wallet Address:').pack(pady=(10,0))
        
        address_frame = ttk.Frame(tab)  # Adres ve paste butonu için bir frame oluştur
        address_frame.pack(pady=(0,10))

        target_address_entry = ttk.Entry(address_frame, width=60)
        target_address_entry.pack(side=tk.LEFT, padx=(0, 5))  # Entry widget'ı sola yasla

        style = ttk.Style()
        style.configure('Small.TButton', font=('Helvetica', 8), padding=2)
        
        paste_button = ttk.Button(address_frame, text="Paste", style='Small.TButton', command=lambda: paste_to_entry(target_address_entry, root))
        paste_button.pack(side=tk.LEFT)  # Paste butonunu entry'nin yanına yerleştir



        ttk.Label(tab, text='Amount:').pack(pady=(10,0))
        amount_entry_transfer = ttk.Entry(tab, width=20)
        amount_entry_transfer.pack(pady=(0,10))

        max_button = ttk.Button(tab, text="Max", command=lambda: update_max_amount(amount_entry_transfer, symhony_address, root))
        max_button.pack(pady=(5, 10))

        ttk.Label(tab, text='Gas (units):').pack(pady=(10,0))
        gas_entry = ttk.Entry(tab, width =20)
        gas_entry.insert(0, "250000")
        gas_entry.pack(pady=(0,10))

        ttk.Label(tab, text='Fee (amount):').pack(pady=(10,0))
        fee_entry = ttk.Entry(tab, width =20)
        fee_entry.insert(0, "900")
        fee_entry.pack(pady=(0,10))

        # Transfer butonu
        transfer_button = ttk.Button(tab, text='Transfer', command=lambda: perform_transfer(amount_entry_transfer, target_address_entry, fee_entry, gas_entry, symhony_address, private_key, root,balance_label))
        transfer_button.pack(pady=(10,20))
        
    elif action_type == "Delegate":
        ttk.Label(tab, text='Validator:').pack(pady=(10,0))
        validator_combobox = ttk.Combobox(tab, values=[v[0] for v in validators], state='readonly', width=40)
        validator_combobox.pack(pady=(0,10))
        validator_combobox.bind('<<ComboboxSelected>>', lambda event: on_validator_selected(event, validators, validator_combobox, symhony_address, private_key))

        ttk.Label(tab, text='Amount:').pack(pady=(10,0))
        amount_entry_delegate = ttk.Entry(tab, width=20)
        amount_entry_delegate.pack (pady=(0,10))
        
        max_button = ttk.Button(tab, text="Max", command=lambda: update_max_amount(amount_entry_delegate, symhony_address, root))
        max_button.pack(pady=(5, 10))

        ttk.Label(tab, text='Gas (units):').pack(pady=(10,0))
        gas_entry = ttk.Entry(tab, width=20)
        gas_entry.insert(0, "250000")  # Sabit değer olarak gas miktarı
        gas_entry.pack(pady=(0,10))

        ttk.Label(tab, text='Fee (amount):').pack(pady=(10,0))
        fee_entry = ttk.Entry(tab, width=20)
        fee_entry.insert(0, "900")  # Sabit değer olarak fee miktarı
        fee_entry.pack(pady=(0,10))

        delegate_button = ttk.Button(tab, text='Delegate', command=lambda: perform_delegate(valid_adr, amount_entry_delegate, gas_entry, fee_entry, symhony_address, private_key, root,balance_label))
        delegate_button.pack(pady=(10,20))
        
    
    
    


    

def on_validator_selected(event, validators, combobox, symhony_address, private_key):
    selected_index = combobox.current()
    target_validator_address = validators[selected_index][1]  # İlgili validator adresini al
    print(f"Selected validator address: {target_validator_address}")
    global valid_adr
    valid_adr=target_validator_address
    

