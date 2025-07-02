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

### 3. 검색 결과 XSS 취약점 해결

-   [ ] **`dangerouslySetInnerHTML` 제거**: `src/app/(protected)/search/page.tsx` 파일에서 `dangerouslySetInnerHTML` 사용을 제거합니다.
-   [ ] **CSS로 스타일링**: 줄 바꿈 처리를 위해 `white-space: pre-wrap;` CSS 속성을 사용하도록 변경합니다.
-   [ ] **(선택) HTML 소독**: 만약 HTML 렌더링이 필수적이라면, `DOMPurify`와 같은 라이브러리를 사용하여 서버로부터 받은 데이터를 클라이언트에서 렌더링하기 전에 소독(sanitize)하는 로직을 추가합니다.

### 4. 로그아웃 처리 흐름 개선

-   [ ] **`useAuth` 훅 수정**: `src/hooks/use-auth.ts`의 `logout` 함수에서 백엔드 API를 먼저 호출하여 서버 세션을 무효화한 후, 성공 시 클라이언트 `signOut`을 호출하도록 순서를 변경합니다.

### 5. Docker 빌드 보안 강화

-   [ ] **`.dockerignore` 파일 수정**: `next-connect-ui/.dockerignore` 파일에 `.env` 및 `.env.*`를 추가하여 민감한 환경 변수 파일이 Docker 이미지에 포함되지 않도록 방지합니다.
