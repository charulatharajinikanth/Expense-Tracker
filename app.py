from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
import csv
import io

app = Flask(__name__)


def create_database():
    connection = sqlite3.connect("expenses.db")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            type TEXT,
            category TEXT
        )
    """)

    connection.commit()
    connection.close()
@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):

    connection = sqlite3.connect("expenses.db")

    connection.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))
@app.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):

    connection = sqlite3.connect("expenses.db")

    if request.method == "POST":
        amount = request.form["amount"]
        transaction_type = request.form["type"]
        category = request.form["category"]

        connection.execute(
            "UPDATE transactions SET amount = ?, type = ?, category = ? WHERE id = ?",
            (amount, transaction_type, category, transaction_id)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("home"))

    transaction = connection.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,)
    ).fetchone()

    connection.close()

    return render_template("edit.html", transaction=transaction)
@app.route("/export")
def export_transactions():
    connection = sqlite3.connect("expenses.db")

    transactions = connection.execute(
        "SELECT id, amount, type, category FROM transactions ORDER BY id DESC"
    ).fetchall()

    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Amount", "Type", "Category"])
    writer.writerows(transactions)

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=transactions.csv"
        }
    )
    
@app.route("/", methods=["GET", "POST"])
def home():
    

    message = ""
    search = request.args.get("search", "")

    if request.method == "POST":
        amount = request.form["amount"]
        transaction_type = request.form["type"]
        category = request.form["category"]

        connection = sqlite3.connect("expenses.db")

        connection.execute(
            "INSERT INTO transactions (amount, type, category) VALUES (?, ?, ?)",
            (amount, transaction_type, category)
        )

        connection.commit()
        connection.close()

        message = f"Saved: ₹{amount} - {transaction_type} - {category}"

    connection = sqlite3.connect("expenses.db")

    if search:
        transactions = connection.execute(
            "SELECT * FROM transactions WHERE category LIKE ? ORDER BY id DESC",
            ("%" + search + "%",)
        ).fetchall()
    else:
        transactions = connection.execute(
            "SELECT * FROM transactions ORDER BY id DESC"
        ).fetchall()

    total_income = connection.execute(
        "SELECT SUM(amount) FROM transactions WHERE type = 'Income'"
    ).fetchone()[0] or 0

    total_expense = connection.execute(
        "SELECT SUM(amount) FROM transactions WHERE type = 'Expense'"
    ).fetchone()[0] or 0

    balance = total_income - total_expense
    expense_data = connection.execute(
    "SELECT category, SUM(amount) FROM transactions "
    "WHERE type = 'Expense' GROUP BY category"
).fetchall()

    connection.close()

    return render_template(
        "index.html",
        message=message,
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        expense_data=expense_data
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
