import streamlit as st
import duckdb
import pandas as pd
import time

# DB 연결 (읽기/쓰기 가능)
conn = duckdb.connect("madang.db", read_only=False)

st.title("📚 Madang DB Manager (신규 고객 등록 + 주문 입력)")

tab1, tab2, tab3 = st.tabs(["고객 조회", "거래 입력", "신규 고객 등록"])

# -------------------------------
# Tab1: 기존 고객 조회
# -------------------------------
with tab1:
    name = st.text_input("검색할 고객명 입력", key="search_name")
    if st.button("검색", key="search_button"):
        if name.strip():
            try:
                sql = """
                    SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice
                    FROM Customer c
                    JOIN Orders o ON c.custid = o.custid
                    JOIN Book b ON b.bookid = o.bookid
                    WHERE c.name LIKE ?
                    ORDER BY o.orderdate DESC
                """
                df = conn.execute(sql, (f"%{name}%",)).df()
                st.dataframe(df)
            except Exception as e:
                st.error(f"조회 에러: {str(e)}")
        else:
            st.warning("고객명을 입력하세요.")

# -------------------------------
# Tab2: 기존 고객 거래 입력
# -------------------------------
with tab2:
    try:
        customers = conn.sql("SELECT custid, name FROM Customer ORDER BY name").df()
        cust_label = customers.apply(lambda r: f"{r['custid']} — {r['name']}", axis=1).tolist()
        selected_cust = st.selectbox("고객 선택", ["선택하세요"] + cust_label, key="existing_customer")
        
        if selected_cust != "선택하세요":
            custid = int(selected_cust.split(" — ")[0])
            st.write(f"선택된 고객번호: {custid}")
            
            books = conn.sql("SELECT bookid, bookname FROM Book ORDER BY bookname").df()
            books['label'] = books['bookid'].astype(str) + " — " + books['bookname']
            selected_book = st.selectbox("구매 서적", ["선택하세요"] + books['label'], key="existing_book")
            
            price = st.text_input("금액 입력", key="existing_price")
            
            if st.button("거래 입력", key="order_button"):
                if selected_book != "선택하세요" and price.isdigit():
                    bookid = int(selected_book.split(" — ")[0])
                    orderid = conn.sql("SELECT COALESCE(MAX(orderid),0)+1 FROM Orders").fetchone()[0]
                    today = time.strftime("%Y-%m-%d")
                    conn.execute(
                        "INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) VALUES (?, ?, ?, ?, ?)",
                        (orderid, custid, bookid, int(price), today)
                    )
                    conn.commit()
                    st.success("거래가 저장되었습니다!")
                else:
                    st.error("책과 금액을 올바르게 선택/입력하세요.")
    except Exception as e:
        st.error(f"기존 고객 거래 입력 에러: {str(e)}")

# -------------------------------
# Tab3: 신규 고객 등록 + 주문
# -------------------------------
with tab3:
    st.subheader("신규 고객 등록 및 주문")
    new_name = st.text_input("새 고객명 입력", key="new_cust")
    new_book_name = st.text_input("새 책 이름 입력", key="new_book")
    new_price = st.text_input("가격 입력", key="new_price")
    
    if st.button("신규 고객 등록 및 주문", key="new_customer_button"):
        try:
            if new_name.strip() and new_book_name.strip() and new_price.isdigit():
                # 신규 고객 ID 생성
                new_custid = conn.sql("SELECT COALESCE(MAX(custid),0)+1 FROM Customer").fetchone()[0]
                conn.execute(
                    "INSERT INTO Customer (custid, name) VALUES (?, ?)",
                    (new_custid, new_name.strip())
                )
                
                # 신규 책 ID 생성
                new_bookid = conn.sql("SELECT COALESCE(MAX(bookid),0)+1 FROM Book").fetchone()[0]
                conn.execute(
                    "INSERT INTO Book (bookid, bookname) VALUES (?, ?)",
                    (new_bookid, new_book_name.strip())
                )
                
                # 신규 주문 생성
                new_orderid = conn.sql("SELECT COALESCE(MAX(orderid),0)+1 FROM Orders").fetchone()[0]
                today = time.strftime("%Y-%m-%d")
                conn.execute(
                    "INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) VALUES (?, ?, ?, ?, ?)",
                    (new_orderid, new_custid, new_bookid, int(new_price), today)
                )
                
                conn.commit()
                st.success(f"신규 고객 '{new_name}' 등록 및 주문 완료!")
            else:
                st.error("모든 정보를 올바르게 입력해야 합니다.")
        except Exception as e:
            st.error(f"신규 고객 등록/주문 에러: {str(e)}")
