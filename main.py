import csv
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

console = Console()

FORMAT_CASU = "%Y-%m-%d %H:%M"


def nacti_dochazku(nazev_souboru):
    dochazka = []

    with open(nazev_souboru, "r", encoding="utf-8-sig", newline="") as soubor:
        reader = csv.DictReader(soubor, delimiter=";")
        for row in reader:
            dochazka.append(row)

    return dochazka


def spocitej_minuty(prichod, odchod):
    """Vrátí délku pobytu v minutách."""
    rozdil = datetime.strptime(odchod, FORMAT_CASU) - datetime.strptime(prichod, FORMAT_CASU)
    return int(rozdil.total_seconds() // 60)


def format_minut(minuty):
    """Převede minuty na text ve formátu H:MM."""
    return f"{minuty // 60}:{minuty % 60:02d}"


def format_data(den):
    return f"{den.day}. {den.month}. {den.year}"


def seskup_po_dnech(dochazka):
    """Vrátí slovník {datum: [záznamy z toho dne]}."""
    po_dnech = {}
    for zaznam in dochazka:
        den = datetime.strptime(zaznam["prichod"], FORMAT_CASU).date()
        if den not in po_dnech:
            po_dnech[den] = []
        po_dnech[den].append(zaznam)
    return po_dnech


# 1 - Docházka po dnech
def zobraz_dochazku(dochazka):
    po_dnech = seskup_po_dnech(dochazka)

    # Pro každý den (seřazeno chronologicky) jedna tabulka
    for den in sorted(po_dnech):
        table = Table(title=f"Docházka {format_data(den)}")
        table.add_column("Čip", justify="right")
        table.add_column("Zaměstnanec", justify="left")
        table.add_column("Příchod", justify="left")
        table.add_column("Odchod", justify="right")
        table.add_column("Počet hodin", justify="center")

        for zaznam in po_dnech[den]:
            prichod = zaznam["prichod"]
            odchod = zaznam["odchod"]
            table.add_row(
                zaznam["cislo_cipu"],
                zaznam["zamestnanec"],
                prichod[11:],  # jen čas HH:MM
                odchod[11:],
                format_minut(spocitej_minuty(prichod, odchod)),
            )

        console.print()
        console.print(table)


# 2 - První a poslední příchod
def zobraz_prichody(dochazka):
    po_dnech = seskup_po_dnech(dochazka)

    table = Table(title="První a poslední příchod po dnech")
    table.add_column("Datum", justify="left")
    table.add_column("První příchod", justify="left")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Poslední příchod", justify="left")
    table.add_column("Zaměstnanec", justify="left")

    for den in sorted(po_dnech):
        # Datum a čas ve formátu RRRR-MM-DD HH:MM se dají porovnávat jako text
        prvni = min(po_dnech[den], key=lambda z: z["prichod"])
        posledni = max(po_dnech[den], key=lambda z: z["prichod"])
        table.add_row(
            format_data(den),
            prvni["prichod"][11:],
            prvni["zamestnanec"],
            posledni["prichod"][11:],
            posledni["zamestnanec"],
        )

    console.print()
    console.print(table)


# 3 - První a poslední odchod
def zobraz_odchody(dochazka):
    po_dnech = seskup_po_dnech(dochazka)

    table = Table(title="První a poslední odchod po dnech")
    table.add_column("Datum", justify="left")
    table.add_column("První odchod", justify="left")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Poslední odchod", justify="left")
    table.add_column("Zaměstnanec", justify="left")

    for den in sorted(po_dnech):
        prvni = min(po_dnech[den], key=lambda z: z["odchod"])
        posledni = max(po_dnech[den], key=lambda z: z["odchod"])
        table.add_row(
            format_data(den),
            prvni["odchod"][11:],
            prvni["zamestnanec"],
            posledni["odchod"][11:],
            posledni["zamestnanec"],
        )

    console.print()
    console.print(table)


# 4 - Celkem odpracovaných hodin
def zobraz_celkem_hodin(dochazka):
    # {čip: [jméno, počet dní, minuty celkem]}
    souhrn = {}
    for zaznam in dochazka:
        cip = zaznam["cislo_cipu"]
        if cip not in souhrn:
            souhrn[cip] = [zaznam["zamestnanec"], 0, 0]
        souhrn[cip][1] += 1
        souhrn[cip][2] += spocitej_minuty(zaznam["prichod"], zaznam["odchod"])

    table = Table(title="Celkem odpracovaných hodin")
    table.add_column("Čip", justify="right")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Počet dnů", justify="center")
    table.add_column("Celkem hodin", justify="center")

    celkem_minut = 0
    for cip in sorted(souhrn):
        jmeno, dny, minuty = souhrn[cip]
        celkem_minut += minuty
        table.add_row(cip, jmeno, str(dny), format_minut(minuty))

    table.add_section()
    table.add_row("", "[bold]Celkem[/bold]", "", f"[bold]{format_minut(celkem_minut)}[/bold]")

    console.print()
    console.print(table)


# 5 - Najít zaměstnance dle čipu
def najdi_zamestnance(dochazka):
    cip = input("Číslo čipu: ").strip()
    zaznamy = [z for z in dochazka if z["cislo_cipu"] == cip]

    if not zaznamy:
        console.print(f"[red]Čip {cip} nebyl nalezen.[/red]")
        return

    table = Table(title=f"Zaměstnanec: {zaznamy[0]['zamestnanec']} (čip {cip})")
    table.add_column("Datum", justify="left")
    table.add_column("Příchod", justify="left")
    table.add_column("Odchod", justify="right")
    table.add_column("Počet hodin", justify="center")

    celkem_minut = 0
    for zaznam in zaznamy:
        minuty = spocitej_minuty(zaznam["prichod"], zaznam["odchod"])
        celkem_minut += minuty
        den = datetime.strptime(zaznam["prichod"], FORMAT_CASU).date()
        table.add_row(
            format_data(den),
            zaznam["prichod"][11:],
            zaznam["odchod"][11:],
            format_minut(minuty),
        )

    table.add_section()
    table.add_row("[bold]Celkem[/bold]", "", "", f"[bold]{format_minut(celkem_minut)}[/bold]")

    console.print()
    console.print(table)


def menu():
    console.print()
    console.rule("[bold blue]ANALÝZA DOCHÁZKY[/bold blue]")
    console.print()
    console.print("1 - Zobrazit docházku po dnech")
    console.print("2 - První a poslední příchod")
    console.print("3 - První a poslední odchod")
    console.print("4 - Celkem odpracovaných hodin")
    console.print("5 - Najít zaměstnance dle čipu")
    console.print("0 - Konec")


def main():
    dochazka = nacti_dochazku(sys.argv[1])

    while True:
        menu()
        volba = input("\nVolba: ").strip()
        if volba == "1":
            zobraz_dochazku(dochazka)
        elif volba == "2":
            zobraz_prichody(dochazka)
        elif volba == "3":
            zobraz_odchody(dochazka)
        elif volba == "4":
            zobraz_celkem_hodin(dochazka)
        elif volba == "5":
            najdi_zamestnance(dochazka)
        elif volba == "0":
            break
        else:
            console.print("[red]Neplatná volba.[/red]")


if __name__ == "__main__":
    main()