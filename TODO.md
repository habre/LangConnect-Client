# TODO List - next-connect-ui 코드 검수

이 문서는 `next-connect-ui` 코드 검토 후 발견된 잠재적 문제점 및 개선 사항을 정리한 것입니다.

---

### 1. 문서 페이지 성능 최적화

-   [ ] **백엔드 API 수정**: `/collections` 엔드포인트가 각 컬렉션의 문서 및 청크 개수를 함께 반환하도록 개선합니다. (N+1 문제 해결)
-   [ ] **프론트엔드 수정**: `src/app/(protected)/documents/page.tsx`의 `fetchCollections` 함수에서 클라이언트 측 계산 로직을 제거하고, 백엔드에서 제공하는 통계 데이터를 직접 사용하도록 수정합니다.

### 2. 다중 삭제 로직 효율성 개선

-   [ ] **백엔드 API 개선**: 여러 ID를 배열로 받아 한 번에 처리할 수 있는 Bulk Delete API 엔드포인트를 구현합니다.
    -   예: `DELETE /api/collections/{id}/documents` (body: `{"document_ids": [...]}` 또는 `{"file_ids": [...]}`)
-   [ ] **프론트엔드 수정**: `src/app/(protected)/documents/page.tsx`의 `handleDeleteSelected` 함수에서 여러 항목을 삭제할 때 단일 API 요청으로 처리하도록 수정합니다.