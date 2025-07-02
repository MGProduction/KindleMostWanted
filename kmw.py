import os
import sys

from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
from plyer import notification

#import webbrowser


# Config
BOOKPRICESCSV_FILE = "csv/books_prices"
BOOKCSV_FILE = "csv/books"
HTMLREPORT_FILE = "report.html"
PAGELOAD_TIMEOUT = 60000
PAGERENDER_TIMEOUT = 2500

# Tools
def load_book_list(csv_path=BOOKCSV_FILE):
    try:
      df = pd.read_csv(csv_path+".csv")    
      return dict(zip(df["URL"], zip(df["Title"],df["Author"])))
    except:
      print(f"Can't read {csv_path}.csv file")
      return None

def notify(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=10  # seconds
    )

def get_price(page):
    try:
        price = page.locator("span.a-color-price").first.text_content().strip()
        return price
    except:
        return "N/A"
        
def generate_html_report(csv_path=BOOKPRICESCSV_FILE, html_path=HTMLREPORT_FILE, low_price=2.99):
    df = pd.read_csv(csv_path)

    def style_price(price_str):
        try:            
            
            if "$" in price_str:
                price = float(price_str.replace("$", "").strip())
            elif "€" in price_str:
                price = float(price_str.replace("€", "").replace(",", ".").strip())
            else:
                price = float(price_str.strip())
                
            if price == 0.00:
                return 'style="color: black; background-color: #FCFC00;"'
            elif price <= 0.99:
                return 'style="color: black; background-color: #F8F800;"'
            elif price <= 1.99:
                return 'style="color: black; background-color: #F0F000;"'
            elif price <= 2.99:
                return 'style="color: black; background-color: #E8E800;"'
            elif price <= 3.99:
                return 'style="color: black; background-color: #E0E000;"'
            elif price <= 4.99:
                return 'style="color: black; background-color: #D8D800;"'
        except:
            pass
        return ""

    rows = ""
    for _, row in df.iterrows():
        price_style = style_price(row["Current Price"])
        author = row["Author"]
        title = row["Title"]
        url = row["URL"]
        price = row["Current Price"]
        rows += f"<tr><td><a href='{url}' target='_blank'>{title}</a></td><td>{author}</td><td {price_style}>{price}</td></tr>\n"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Kindle Price Tracker</title>
    <style>
        body {{ font-family: sans-serif; padding: 1em; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 0.5em; text-align: left; }}
        th {{ background-color: #eee; cursor: pointer;}}
        .sr-only {{  position: absolute;  top: -30em;}}        
        table.sortable th {{  font-weight: bold;  border-bottom: thin solid #888;  position: relative;}}
        table.sortable th.no-sort {{  padding-top: 0.35em;}}
        table.sortable th:nth-child(5) {{  width: 10em;}}
        table.sortable th button {{  padding: 4px;  margin: 1px;  font-size: 100%;  font-weight: bold;  background: transparent;  border: none;  display: inline;  right: 0;  left: 0;  top: 0;  bottom: 0;  width: 100%;  text-align: left;  outline: none;  cursor: pointer;}}
        table.sortable th button span {{  position: absolute;  right: 4px;}}
        table.sortable th[aria-sort="descending"] span::after {{  content: "▼";  color: currentcolor;  font-size: 100%;  top: 0;}}
        table.sortable th[aria-sort="ascending"] span::after {{  content: "▲";  color: currentcolor;  font-size: 100%;  top: 0;}}
        table.show-unsorted-icon th:not([aria-sort]) button span::after {{  content: "♢";  color: currentcolor;  font-size: 100%;  position: relative;  top: -3px;  left: -4px;}}
        table.sortable td.num {{  text-align: right;}}
        table.sortable tbody tr:nth-child(odd) {{  background-color: #ddd;}}
        /* Focus and hover styling */
        table.sortable th button:focus,table.sortable th button:hover {{  padding: 2px;  border: 2px solid currentcolor;  background-color: #e5f4ff;}}
        table.sortable th button:focus span,table.sortable th button:hover span {{ right: 2px;}}
        table.sortable th:not([aria-sort]) button:focus span::after,table.sortable th:not([aria-sort]) button:hover span::after {{content: "▼"; color: currentcolor;  font-size: 100%;  top: 0;}}    
    </style>
   	<script>
/*
 *   From: https://www.w3.org/WAI/ARIA/apg/patterns/table/examples/sortable-table/#aboutthisexample
 *   This content is licensed according to the W3C Software License at
 *   https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document
 *
 *   File:   sortable-table.js
 *
 *   Desc:   Adds sorting to a HTML data table that implements ARIA Authoring Practices
 */    
    'use strict';
    class SortableTable {{
      constructor(tableNode) {{
        this.tableNode = tableNode;
        this.columnHeaders = tableNode.querySelectorAll('thead th');
        this.sortColumns = [];
        for (var i = 0; i < this.columnHeaders.length; i++) {{
          var ch = this.columnHeaders[i];
          var buttonNode = ch.querySelector('button');
          if (buttonNode) {{
            this.sortColumns.push(i);
            buttonNode.setAttribute('data-column-index', i);
            buttonNode.addEventListener('click', this.handleClick.bind(this));
          }}
        }}
        this.optionCheckbox = document.querySelector(
          'input[type="checkbox"][value="show-unsorted-icon"]'
        );
        if (this.optionCheckbox) {{
          this.optionCheckbox.addEventListener(
            'change',
            this.handleOptionChange.bind(this)
          );
          if (this.optionCheckbox.checked) {{
            this.tableNode.classList.add('show-unsorted-icon');
          }}
        }}
      }}
      setColumnHeaderSort(columnIndex) {{
        if (typeof columnIndex === 'string') {{
          columnIndex = parseInt(columnIndex);
        }}
        for (var i = 0; i < this.columnHeaders.length; i++) {{
          var ch = this.columnHeaders[i];
          var buttonNode = ch.querySelector('button');
          if (i === columnIndex) {{
            var value = ch.getAttribute('aria-sort');
            if (value === 'descending') {{
              ch.setAttribute('aria-sort', 'ascending');
              this.sortColumn(
                columnIndex,
                'ascending',
                ch.classList.contains('num')
              );
            }} else {{
              ch.setAttribute('aria-sort', 'descending');
              this.sortColumn(
                columnIndex,
                'descending',
                ch.classList.contains('num')
              );
            }}
          }} else {{
            if (ch.hasAttribute('aria-sort') && buttonNode) {{
              ch.removeAttribute('aria-sort');
            }}
          }}
        }}
      }}
      sortColumn(columnIndex, sortValue, isNumber) {{
        function compareValues(a, b) {{
          if (sortValue === 'ascending') {{
            if (a.value === b.value) {{
              return 0;
            }} else {{
              if (isNumber) {{
                return a.value - b.value;
              }} else {{
                return a.value < b.value ? -1 : 1;
              }}
            }}
          }} else {{
            if (a.value === b.value) {{
              return 0;
            }} else {{
              if (isNumber) {{
                return b.value - a.value;
              }} else {{
                return a.value > b.value ? -1 : 1;
              }}
            }}
          }}
        }}
        if (typeof isNumber !== 'boolean') {{
          isNumber = false;
        }}
        var tbodyNode = this.tableNode.querySelector('tbody');
        var rowNodes = [];
        var dataCells = [];
        var rowNode = tbodyNode.firstElementChild;
        var index = 0;
        while (rowNode) {{
          rowNodes.push(rowNode);
          var rowCells = rowNode.querySelectorAll('th, td');
          var dataCell = rowCells[columnIndex];

          var data = {{}};
          data.index = index;
          data.value = dataCell.textContent.toLowerCase().trim();
          if (isNumber) {{
            data.value = parseFloat(data.value);
          }}
          dataCells.push(data);
          rowNode = rowNode.nextElementSibling;
          index += 1;
        }}
        dataCells.sort(compareValues);
        // remove rows
        while (tbodyNode.firstChild) {{
          tbodyNode.removeChild(tbodyNode.lastChild);
        }}
        // add sorted rows
        for (var i = 0; i < dataCells.length; i += 1) {{
          tbodyNode.appendChild(rowNodes[dataCells[i].index]);
        }}
      }}
      /* EVENT HANDLERS */
      handleClick(event) {{
        var tgt = event.currentTarget;
        this.setColumnHeaderSort(tgt.getAttribute('data-column-index'));
      }}
      handleOptionChange(event) {{
        var tgt = event.currentTarget;

        if (tgt.checked) {{
          this.tableNode.classList.add('show-unsorted-icon');
        }} else {{
          this.tableNode.classList.remove('show-unsorted-icon');
        }}
      }}
    }}
    // Initialize sortable table buttons
    window.addEventListener('load', function () {{
      var sortableTables = document.querySelectorAll('table.sortable');
      for (var i = 0; i < sortableTables.length; i++) {{
        new SortableTable(sortableTables[i]);
      }}
    }});
	</script>
</head>
<body>
    <h2>Kindle Price Tracker - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</h2>
    <table class="sortable">
        <thead><tr>
                <th aria-sort="ascending"><button>Title<span aria-hidden="true"></span></button></th>
                <th aria-sort="ascending"><button>Author<span aria-hidden="true"></span></button></th>                
                <th class="num"><button>Price<span aria-hidden="true"></span></button></th></tr></thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML report written to: {html_path}")
        
# Program
def main():
    METACMD = ""
    BOOKCSV = BOOKCSV_FILE
    if len(sys.argv)>1:
        BOOKCSV=sys.argv[1].replace(".csv", "").strip()
    if len(sys.argv)>2:
        METACMD=sys.argv[2].strip()        
    BOOKPRICECSV=BOOKCSV+"_prices.csv"
    BOOKPRICEREPORT=BOOKCSV+"_prices.html"

    if METACMD!="*":        
        # read input CSV
        BOOK_URLS = load_book_list(BOOKCSV)

        if not BOOK_URLS:
            print("Usage: kmw.py <book list csv>")
            print("       with [Author, Title, Url]")
        else:
            update_count = 0
            # read / create output CSV
            if os.path.exists(BOOKPRICECSV):
                df = pd.read_csv(BOOKPRICECSV)
            else:
                df = pd.DataFrame(columns=["Author","Title", "URL", "Previous Price", "Current Price", "Last Checked"])
            # scan amazon pages to get current price
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                updated = []
                try:
                  for url, titleauthor in BOOK_URLS.items():
                      title=titleauthor[0]
                      author=titleauthor[1]
                      print(f"Checking: {title}")
                      page.goto(url, timeout=PAGELOAD_TIMEOUT)
                      page.wait_for_timeout(PAGERENDER_TIMEOUT)
                      #page.wait_for_selector("span.a-color-price", timeout=PAGELOAD_TIMEOUT)                
                      current_price = get_price(page)
                      prev_row = df[df["Title"] == title]
                      previous = prev_row["Current Price"].values[0] if not prev_row.empty else "N/A"
                      changed = current_price != previous
                      if changed:
                          print(f"  ➜ Price changed: {previous} → {current_price}")
                          if previous!="N/A":
                              shorttitle=title
                              if len(shorttitle)>24:
                                  shorttitle=title[:20]+"..."
                              notify(f"Price Drop: {shorttitle}", f"{previous} → {current_price}")                
                      else:
                          print(f"  = No change: {current_price}")
                      update_count=update_count+1
                      updated.append({
                          "Author": author,
                          "Title": title,
                          "URL": url,
                          "Previous Price": previous,
                          "Current Price": current_price,
                          "Last Checked": datetime.now()
                      })
                except:
                    print("errors in csv file (wrong format?)")

                browser.close()
            if update_count:
                # write output CSV
                pd.DataFrame(updated).to_csv(BOOKPRICECSV, index=False)
            
                # write output HMTL from CSV
                generate_html_report(BOOKPRICECSV,BOOKPRICEREPORT)    
                #webbrowser.open("file://"+BOOKPRICEREPORT) 
            else:
                print("nothing to add/update")

if __name__ == "__main__":
    main()
