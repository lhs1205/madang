import streamlit as st
import duckdb
import pandas as pd
import time

DB_PATH = "madang.db"  # repo에 포함할 파일

# 연결 (read_only=False -> 쓰기 가능)
conn = duckdb.connect(DB_PATH, read_only=False)

st.set_page_config(page_title="Madang Manager", layout="wide")
st.title("📚 Madang Manager (DuckDB)")

tab1, tab2, tab3 = st.tabs(["고객 조회", "거래 입력", "데이터 관리"])

# -------------------------
# Helper functions
# -------------------------
def run_df(sql, params=None):
    if params:
        return conn.execute(sql, params).df()
    return conn.sql(sql).df()

def run_exec(sql, params=None):
    if params:
        conn.execute(sql, params)
    else:
        conn.execute(sql)
    conn.commit()

# -------------------------
# Tab1: 고객 조회
# -------------------------
with tab1:
    name = st.text_input("고객명 입력 (이름 일부 가능)")
    if st.button("검색"):
        if name.strip() == "":
            st.warning("이름을 입력하세요.")
        else:
            sql = """
            SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice
            FROM Customer c
            JOIN Orders o ON c.custid = o.custid
            JOIN Book b ON b.bookid = o.bookid
            WHERE c.name LIKE ?
            ORDER BY o.orderdate DESC
            LIMIT 200
            """
            df = run_df(sql, (f"%{name}%",))
            st.dataframe(df)

# -------------------------
# Tab2: 거래 입력
# -------------------------
with tab2:
    st.subheader("거래 입력 (새 주문)")
    # 고객 선택: 전체 고객 로드(혹은 검색 기능 추가)
    customers = run_df("SELECT custid, name FROM Customer ORDER BY name")
    customer_label = customers.apply(lambda r: f"{r['custid']} — {r['name']}", axis=1).tolist()
    sel_cust = st.selectbox("고객 선택", ["선택하세요"] + customer_label)
    if sel_cust != "선택하세요":
        custid = int(sel_cust.split(" — ")[0])
        st.write(f"선택된 고객번호: {custid}")

        # 책 목록
        books = run_df("SELECT bookid, bookname FROM Book ORDER BY bookname")
        book_label = books.apply(lambda r: f"{r['bookid']} — {r['bookname']}", axis=1).tolist()
        sel_book = st.selectbox("구매 서적", ["선택하세요"] + book_label)

        price = st.text_input("금액", value="")
        if st.button("거래 입력"):
            # 유효성 검사
            if sel_book == "선택하세요" or price.strip() == "":
                st.error("책과 금액을 선택/입력하세요.")
            elif not price.isdigit():
                st.error("금액은 숫자만 입력하세요.")
            else:
                bookid = int(sel_book.split(" — ")[0])
                today = time.strftime("%Y-%m-%d")
                # 안전한 orderid 생성 (동시성 완화: 트랜잭션이 필요하지만 duckdb 단일 프로세스면 보통 OK)
                max_row = run_df("SELECT COALESCE(MAX(orderid), 0) AS maxid FROM Orders")
                next_orderid = int(max_row['maxid'][0]) + 1
                # INSERT (파라미터 바인딩)
                run_exec("INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) VALUES (?, ?, ?, ?, ?)",
                         (next_orderid, custid, bookid, int(price), today))
                st.success("거래가 입력되었습니다.")
                st.write(f"OrderID: {next_orderid}")

# -------------------------
# Tab3: 데이터 관리 (백업 다운로드 등)
# -------------------------
with tab3:
    st.subheader("데이터 관리")
    st.markdown("***DB 파일 다운로드(현재 컨테이너의 madang.db를 다운로드합니다).***")
    with open(DB_PATH, "rb") as f:
        btn = st.download_button("DB 다운로드", f, file_name="madang.db")
    st.info("주의: Streamlit Cloud 컨테이너가 재시작되면 로컬 변경사항은 사라질 수 있습니다.")
