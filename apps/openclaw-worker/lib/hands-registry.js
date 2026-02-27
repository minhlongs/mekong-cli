/**
 * 🐉 BINH PHÁP v5.0: The Hands Registry (Inspired by OpenFang)
 * Maps intents to specialized Agent "Hands" with unique system prompts.
 */
const HANDS = {
    PLANNER: {
        name: "Planner Hand (Quân Sư)",
        instructions: "🔥 BẠN LÀ PLANNER HAND (QUÂN SƯ). Tập trung vào Architecture, Specification, và BMM Strategic Planning. KHÔNG được implement code cẩu thả. LUÔN LUÔN dùng /plan:hard hoặc /plan:parallel."
    },
    CODER: {
        name: "Coder Hand (Tiên Phong)",
        instructions: "🔥 BẠN LÀ CODER HAND (TIÊN PHONG). Tập trung vào Atomic Implementation, Bug Fixing, và Performance. Kế thừa plan từ Quân Sư. LUÔN LUÔN dùng /cook --fast hoặc /cook --parallel."
    },
    REVIEWER: {
        name: "Reviewer Hand (Ngự Sử)",
        instructions: "🔥 BẠN LÀ REVIEWER HAND (NGỰ SỬ). Tập trung vào Security Audit, QA Gate, và Binh Pháp Certification. KHÔNG được cho qua nếu thiếu test hoặc vi phạm code style."
    }
};

function getHandForIntent(intent) {
    if (intent === 'PLAN' || intent === 'RESEARCH') return HANDS.PLANNER;
    if (intent === 'REVIEW') return HANDS.REVIEWER;
    return HANDS.CODER; // Default to Coder for EXECUTION
}

module.exports = { HANDS, getHandForIntent };
