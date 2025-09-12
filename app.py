from flask import Flask, render_template, request, redirect, url_for, session  # type: ignore # thêm session
import json
from tinh_toan import tinh_toan_key, tu_van_dieu_chinh  # <-- import hàm từ file ngoài

app = Flask(__name__)
app.secret_key = "super_secret_key"  # cần cho session, đặt chuỗi bất kỳ

# nạp vật liệu từ JSON
with open("data/materials.json", "r", encoding="utf-8") as f:
    materials = json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # lấy dữ liệu từ form
        form_data = {
            "d": request.form.get("d", ""),
            "l": request.form.get("l", ""),
            "p": request.form.get("p", ""),
            "n": request.form.get("n", ""),
            "eta": request.form.get("eta", ""),
            "z": request.form.get("z", ""),
            "mat1": request.form.get("mat1", ""),
            "mat2": request.form.get("mat2", "")
        }
        # lưu vào session
        session["form_data"] = form_data
        return redirect(url_for("calculate"))

    # khi load lại trang index, lấy dữ liệu cũ từ session
    form_data = session.get("form_data", {})
    return render_template("index.html", materials=materials, form_data=form_data)

@app.route("/calculate", methods=["GET", "POST"])
def calculate():
    if request.method == "POST":
        d = float(request.form["d"])
        L = float(request.form["L"])
        p = float(request.form["p"])
        n = float(request.form["n"])
        eta = float(request.form["eta"])
        z = int(request.form["z"])
        mat1 = request.form["mat1"]
        mat2 = request.form["mat2"]

        # lưu lại form_data vào session để quay về index có dữ liệu
        session["form_data"] = {
            "d": request.form["d"],
            "L": request.form["L"],
            "p": request.form["p"],
            "n": request.form["n"],
            "eta": request.form["eta"],
            "z": request.form["z"],
            "mat1": mat1,
            "mat2": mat2
        }

        # gọi hàm tính toán thiết kế thông số then
        result = tinh_toan_key(d, L, p, n, eta, z, mat1, mat2)
        # gọi hàm tư vấn
        tu_van = tu_van_dieu_chinh(d, L, p, n, eta, z, mat1, mat2)
        result["tu_van"] = tu_van


        # Dữ liệu vẽ biểu đồ
        start = int(round(d)) - 5
        d_values = list(range(start, start + 11))  # length 11: d-5 .. d .. d+5

        sf11_values = []
        sf12_values = []
        sf21_values = []
        sf22_values = []

        for d_test in d_values:
            if d_test <= 0:
                sf11_values.append(None)
                sf12_values.append(None)
                sf21_values.append(None)
                sf22_values.append(None)
                continue

            res = tinh_toan_key(d_test, L, p, n, eta, z, mat1, mat2)
            # nếu có lỗi (ví dụ "Error" key) thì push None
            if all(k in res for k in ("sf11", "sf12", "sf21", "sf22")):
                sf11_values.append(round(res["sf11"], 2) if res["sf11"] is not None else None)
                sf12_values.append(round(res["sf12"], 2) if res["sf12"] is not None else None)
                sf21_values.append(round(res["sf21"], 2) if res["sf21"] is not None else None)
                sf22_values.append(round(res["sf22"], 2) if res["sf22"] is not None else None)
            else:
                sf11_values.append(None)
                sf12_values.append(None)
                sf21_values.append(None)
                sf22_values.append(None)

        # truyền thêm 4 list và tên vật liệu vào template
        return render_template("result.html",
                            result=result,
                            d_values=d_values,
                            sf11_values=sf11_values,
                            sf12_values=sf12_values,
                            sf21_values=sf21_values,
                            sf22_values=sf22_values,
                            mat1=mat1,
                            mat2=mat2)    
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True) #để Fault khi show cho client. Khi test để True để server tự reload
