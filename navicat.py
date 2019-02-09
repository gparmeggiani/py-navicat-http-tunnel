"""
Copyright (C) Giacomo Parmeggiani - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Author: Giacomo Parmeggiani <giacomo.parmeggiani@gmail.com>
Date:   October 2018

"""
import struct
import sqlite3
import base64


def _pack_ulong(val):
    return struct.pack(">I", int(val))


def _pack_ushort(val):
    return struct.pack(">H", val)


def _gen_padding(count):
    ret_str = b''
    for i in range(0, count):
        ret_str += b'\x00'
    return ret_str


def _gen_block(val):
    if isinstance(val, str):
        val = val.encode()
    val_len = len(val)
    if val_len < 254:
        return bytes([val_len])+val
    else:
        return b'\xFE'+_pack_ulong(val_len)+val


def _gen_header(errno):
    ret = _pack_ulong(1111)
    ret += _pack_ushort(202)
    ret += _pack_ulong(errno)
    ret += _gen_padding(6)

    return ret


def _gen_conn_info():
    ret = _gen_block(sqlite3.version.encode())
    ret += _gen_block(sqlite3.version.encode())
    ret += _gen_block(sqlite3.version.encode())

    return ret


def _gen_result_set_header(errno, affected_rows, insert_id, num_fields, num_rows):

    ret = _pack_ulong(errno)
    ret += _pack_ulong(affected_rows)
    ret += _pack_ulong(insert_id)
    ret += _pack_ulong(num_fields)
    ret += _pack_ulong(num_rows)
    ret += _gen_padding(12)

    return ret


def _gen_fields_header(rows):
    ret = b''
    for key in rows[0].keys():
        ret += _gen_block(key)
        ret += _gen_block("")
        # 5 is SQLITE3_NULL
        ret += _pack_ulong(5)
        ret += _pack_ulong(0)
        ret += _pack_ulong(0)

    return ret


def _gen_data(rows):
    ret = b''

    for row in rows:
        for col in row:
            # 5 is SQLITE3_NULL
            col_type = 5
            if col is None:
                ret += b'\xFF'
            else:
                if isinstance(col, str):
                    # SQLITE3_TEXT
                    col_type = 3
                elif isinstance(col, int):
                    # SQLITE3_INTEGER
                    col_type = 1
                elif isinstance(col, float):
                    # SQLITE3_FLOAT
                    col_type = 2
                else:
                    # SQLITE3_BLOB
                    col_type = 4

                ret += _gen_block(str(col))

            ret += _pack_ulong(col_type)

    return ret


def build_error_response(errno, errmsg):
    resp = _gen_header(errno)
    resp += _gen_block(errmsg)

    return resp


def on_request(db_filename, action, query, is_base64_encoded=False):

    try:
        conn = sqlite3.connect(db_filename)
        conn.row_factory = sqlite3.Row

    except sqlite3.Error as e:
        return build_error_response(202, e.args[0])

    cursor = conn.cursor()

    if action == "C":
        resp = _gen_header(0)
        resp += _gen_conn_info()

    elif action == "Q":
        resp = _gen_header(0)

        queries = query.split('\n')
        for i, query in enumerate(queries):
            error_msg = ""
            errno = 0
            if query == "":
                continue
            if is_base64_encoded:
                query = base64.b64decode(query).decode()

            rows = []
            try:
                res = cursor.execute(query)
                conn.commit()
                rows = res.fetchall()

            except sqlite3.Error as e:
                error_msg = e.args[0]
                errno = 1

            num_rows = len(rows)
            num_fields = 0
            if num_rows:
                num_fields = len(rows[0])
            affected_rows = cursor.rowcount or 0
            insert_id = cursor.lastrowid or 0

            if affected_rows == -1:
                affected_rows = 0

            resp += _gen_result_set_header(
                errno, affected_rows, insert_id, num_fields, num_rows
            )

            if num_fields:
                resp += _gen_fields_header(rows)
                resp += _gen_data(rows)
            elif error_msg:
                resp += _gen_block(error_msg)
            else:
                resp += _gen_block("")

            if i < len(queries) - 1:
                resp += b'\0x01'
            else:
                resp += b'\0x00'
    else:
        resp = _gen_header(202)
        resp += _gen_block("Unsupported action")

    conn.close()
    return resp
