"""Live smoke test of the buyer flow through the real API (calls OpenAI, about $0.005).

Run from backend/:  python -m scripts.smoke_buyer
"""

from fastapi.testclient import TestClient

from app.main import app
from scripts.live_users import throwaway_users

REQUEST = ("Hi, need 10x 6205 sealed bearings and 4 belts A42 for the conveyor, "
           "plus one 1.5kW 4 pole motor foot mount. Urgent.")


def main() -> None:
    client = TestClient(app)
    with throwaway_users(client, 2) as [(alice_id, alice), (bob_id, bob)]:
        me = client.get("/me", headers=alice).json()
        print("me:", me["email"], "|", me["shop"]["name"])

        rfq = client.post("/rfqs/analyze", json={"text": REQUEST}, headers=alice)
        assert rfq.status_code == 201, rfq.text
        rfq = rfq.json()
        print(f"analyzed: {rfq['ai']['model_calls']} AI calls, ${rfq['ai']['cost_usd']:.4f}")
        for line in rfq["lines"]:
            part = line["part"]
            print(f"  {line['quantity']:>3} x {line['description']!r:40} -> {line['match_status']:12} "
                  f"{(part['brand'] + ' ' + part['part_number']) if part else ''}  ({line['match_reason']})")

        # The other user can't see it: Row Level Security returns nothing, the API says 404.
        assert client.get(f"/rfqs/{rfq['id']}", headers=bob).status_code == 404
        assert client.get("/rfqs", headers=bob).json() == []
        print("isolation: bob cannot see alice's RFQ (404)")

        # No login, no access.
        assert client.get("/rfqs").status_code == 401
        print("no token: 401")

        if all(line["part"] for line in rfq["lines"]):
            published = client.post(f"/rfqs/{rfq['id']}/publish", headers=alice)
            assert published.status_code == 200, published.text
            print("published:", published.json()["status"])
    print("users deleted. OK")


if __name__ == "__main__":
    main()
