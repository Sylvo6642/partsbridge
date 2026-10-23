"""Live smoke test of the seller flow through the real API (about $0.0002).

Run from backend/:  python -m scripts.smoke_seller
"""

from fastapi.testclient import TestClient

from app.main import app
from scripts.live_users import throwaway_users


def main() -> None:
    client = TestClient(app)
    with throwaway_users(client, 2) as [(_, seller), (_, other)]:
        inbox = client.get("/seller/inbox", headers=seller).json()
        print("inbox:", [(r["buyer_name"], r["line_count"], r["my_quote_status"]) for r in inbox])
        rfq = inbox[0]

        drafted = client.post(f"/seller/rfqs/{rfq['id']}/draft", headers=seller)
        assert drafted.status_code == 200, drafted.text
        quote = drafted.json()["my_quote"]
        print(f"draft: total ${quote['total']} ({quote['notes']}) ai={quote['ai']}")
        for l in quote["lines"]:
            print(f"   {l['quantity']} x {l['part']['part_number'] if l['part'] else '-'} @ {l['unit_price']} "
                  f"= {l['line_total']}  stock {l['stock_qty']}  {l['note'] or ''}")

        first = quote["lines"][0]
        edited = client.put(f"/quotes/{quote['id']}", headers=seller,
                            json={"lines": [{"id": first["id"], "quantity": first["quantity"], "unit_price": "9.99"}]})
        assert edited.status_code == 200, edited.text
        print("after editing line 1 to $9.99: total", edited.json()["my_quote"]["total"])

        # Another visitor can't touch this quote or see this RFQ.
        assert client.put(f"/quotes/{quote['id']}", headers=other, json={"lines": []}).status_code == 404
        assert client.get(f"/seller/rfqs/{rfq['id']}", headers=other).status_code == 404
        print("isolation: other user gets 404 on the quote and the RFQ")

        submitted = client.post(f"/quotes/{quote['id']}/submit", headers=seller)
        assert submitted.status_code == 200 and submitted.json()["my_quote"]["status"] == "submitted"
        assert client.put(f"/quotes/{quote['id']}", headers=seller, json={"lines": []}).status_code == 409
        print("submitted; editing afterwards is refused (409)")
    print("users deleted. OK")


if __name__ == "__main__":
    main()
