import streamlit as st
import duckdb
import pandas as pd
import time

# DuckDB 파일 연결
conn = duckdb.connect("madang.db", read_only=False)

st.title("📚 Madang DB Manager (DuckDB + Streamlit Cloud)")

tab1, tab2 = st.tabs(["고객 조회", "거래 입력"])

# ------------------------------------------------
# 1. 고객 조회
# ------------------------------------------------
name = tab1.text_input("고객명 입력")

if name:
    sql = f"""
        SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice
        FROM Customer c
        JOIN Orders o ON c.custid = o.custid
        JOIN Book b ON b.bookid = o.bookid
        WHERE c.name = '{name}'
    """

    df = conn.sql(sql).df()
    tab1.dataframe(df)

    if not df.empty:
        custid = df['custid'][0]
        tab2.write(f"고객번호: {custid}")
        tab2.write(f"고객명: {name}")

        # ------------------------------------------------
        # 2. 책 목록 불러오기
        # ------------------------------------------------
        books = conn.sql("SELECT bookid, bookname FROM Book").df()
        books['label'] = books['bookid'].astype(str) + " — " + books['bookname']
        selected = tab2.selectbox("구매 서적", books['label'])

        bookid = int(selected.split(" — ")[0])

        # ------------------------------------------------
        # 3. 금액 입력 & 주문 저장
        # ------------------------------------------------
        price = tab2.text_input("금액 입력")

        if tab2.button("거래 입력"):
            if price.isnumeric():
                orderid = conn.sql("SELECT COALESCE(MAX(orderid), 0) + 1 FROM Orders").fetchone()[0]
                today = time.strftime("%Y-%m-%d")

                conn.execute(
                    f"""
                    INSERT INTO Orders VALUES
                    ({orderid}, {custid}, {bookid}, {price}, '{today}')
                    """
                )
                conn.commit()
                tab2.success("거래가 저장되었습니다!")
            else:
                tab2.error("금액은 숫자로 입력해야 합니다.")
