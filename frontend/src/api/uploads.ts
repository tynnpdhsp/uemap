import { api } from "./client";

export interface UploadImagesResponse {
  object_keys: string[];
  preview_urls: string[];
}

export interface UploadVideoResponse {
  object_key: string;
  preview_url: string;
}

export const uploadsApi = {
  uploadImages: (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    return api.postFormData<UploadImagesResponse>("/uploads/images", formData);
  },

  uploadVideo: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.postFormData<UploadVideoResponse>("/uploads/video", formData);
  },
};
