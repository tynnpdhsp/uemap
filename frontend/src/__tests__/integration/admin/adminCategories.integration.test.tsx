import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { installFetchMock, jsonOk, jsonError } from "../helpers/fetchMock";
import { renderAdminApp } from "../helpers/renderAdminApp";
import { adminProfile, sampleCategories } from "../helpers/adminFixtures";

describe("integration: admin quản lý danh mục", () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem("admin_access_token", "admin-token-123");
  });

  it("hiển thị danh sách danh mục", async () => {
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/categories")) {
        return jsonOk(sampleCategories);
      }
      return null;
    });

    renderAdminApp(["/admin/categories"]);

    expect(await screen.findByText("Quán ăn")).toBeInTheDocument();
    expect(await screen.findByText("Thư viện")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("mở form tạo danh mục khi nhấn nút Tạo danh mục", async () => {
    const user = userEvent.setup();
    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/categories")) {
        return jsonOk(sampleCategories);
      }
      return null;
    });

    renderAdminApp(["/admin/categories"]);

    await screen.findByText("Quán ăn");

    await user.click(screen.getByRole("button", { name: /Tạo danh mục/ }));

    expect(screen.getByText("Tạo danh mục mới")).toBeInTheDocument();
  });

  it("tạo danh mục mới thành công", async () => {
    const user = userEvent.setup();
    let created = false;

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/categories")) {
        const cats = created
          ? [...sampleCategories, { id: "cat003", name: "Phòng học", color: "#22C55E", order: 3, is_hidden: false, place_count: 0, created_at_display: "25/05/2025" }]
          : sampleCategories;
        return jsonOk(cats);
      }
      if (method === "POST" && url.includes("/api/admin/categories")) {
        created = true;
        return jsonOk({ id: "cat003", name: "Phòng học", color: "#22C55E", order: 3, is_hidden: false, place_count: 0, created_at_display: "25/05/2025" });
      }
      return null;
    });

    renderAdminApp(["/admin/categories"]);
    await screen.findByText("Quán ăn");

    await user.click(screen.getByRole("button", { name: /Tạo danh mục/ }));

    const inputs = screen.getAllByRole("textbox");
    const nameInput = inputs.find((el) => el.closest("form"));
    await user.type(nameInput!, "Phòng học");

    fireEvent.submit(screen.getByRole("button", { name: "Tạo mới" }).closest("form")!);

    expect(await screen.findByText("Tạo danh mục thành công.")).toBeInTheDocument();
    expect(await screen.findByText("Phòng học")).toBeInTheDocument();
  });

  it("xóa danh mục có địa điểm hiển thị lỗi", async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => true);

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/categories")) {
        return jsonOk(sampleCategories);
      }
      if (method === "DELETE" && url.includes("/api/admin/categories/cat001")) {
        return jsonError("Không thể xóa danh mục đang có 10 địa điểm.", 409);
      }
      return null;
    });

    window.alert = jest.fn();

    renderAdminApp(["/admin/categories"]);
    await screen.findByText("Quán ăn");

    const deleteButtons = screen.getAllByTitle("Xóa");
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining("Không thể xóa danh mục"),
      );
    });
  });

  it("ẩn/hiển thị danh mục", async () => {
    const user = userEvent.setup();
    let toggledHidden = false;

    installFetchMock((url, method) => {
      if (method === "GET" && url.includes("/api/admin/auth/me")) {
        return jsonOk(adminProfile);
      }
      if (method === "GET" && url.includes("/api/admin/categories")) {
        const cats = toggledHidden
          ? sampleCategories.map((c) => c.id === "cat001" ? { ...c, is_hidden: true } : c)
          : sampleCategories;
        return jsonOk(cats);
      }
      if (method === "PATCH" && url.includes("/api/admin/categories/cat001/hide")) {
        toggledHidden = true;
        return jsonOk({ ...sampleCategories[0], is_hidden: true });
      }
      return null;
    });

    renderAdminApp(["/admin/categories"]);
    await screen.findByText("Quán ăn");

    const hideButtons = screen.getAllByTitle("Ẩn");
    await user.click(hideButtons[0]);

    await waitFor(() => {
      expect(screen.getAllByText("Đang ẩn").length).toBeGreaterThanOrEqual(2);
    });
  });
});
