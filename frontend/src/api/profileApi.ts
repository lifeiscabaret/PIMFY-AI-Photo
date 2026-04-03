const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://223.130.146.245:8000";

export const createAdoptionProfile = async (
    file: File,
    name: string,
    age: string,
    personality: string,
    features: string,
    contact?: string
) => {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("name", name);
    formData.append("age", age);
    formData.append("personality", personality);
    formData.append("features", features);
    if (contact) formData.append("contact", contact);

    const response = await fetch(`${API_BASE_URL}/api/v1/generate-adoption-profile`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) throw new Error("입양 프로필 생성 실패");
    return await response.json();
};

export const createStudioProfile = async (file: File, bgColor: string) => {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("bg_color", bgColor);

    const response = await fetch(`${API_BASE_URL}/api/v1/generate-studio-profile`, {
        method: "POST",
        body: formData,
    });
    if (!response.ok) throw new Error("스튜디오 프로필 생성 실패");
    return await response.json();
};

export const createRealProfile = async (dogUid: number, contact?: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/generate-real-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dog_uid: dogUid, contact: contact }),
    });
    if (!response.ok) throw new Error("자동 프로필 생성 실패");
    return await response.json();
};

export const searchDogs = async (searchTerm: string) => {
    const response = await fetch(`${API_BASE_URL}/api/dogs/search?name=${searchTerm}`);
    if (!response.ok) throw new Error('서버 통신 실패');
    return await response.json();
};
