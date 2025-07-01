export const ko = {
  common: {
    loading: '로딩 중...',
    error: '오류',
    success: '성공',
    cancel: '취소',
    save: '저장',
    delete: '삭제',
    edit: '편집',
    create: '만들기',
    search: '검색',
    refresh: '새로고침',
    logout: '로그아웃',
    none: '없음',
    selectAll: '전체 선택',
    selected: '{{count}}개 선택됨',
    total: '총 {{count}}개',
  },
  sidebar: {
    main: '메인',
    collections: '컬렉션',
    documents: '문서',
    search: '검색',
    apiTester: 'API 테스터',
    mainTitle: '메인'
  },
  collections: {
    title: '컬렉션 관리',
    description: '문서 컬렉션을 생성하고 관리하세요',
    newCollection: '새 컬렉션',
    collectionList: '컬렉션 목록',
    noCollections: '컬렉션이 없습니다',
    noCollectionsDescription: '첫 번째 컬렉션을 생성하여 문서들을 체계적으로 관리해보세요.',
    createFirstCollection: '첫 컬렉션 만들기',
    stats: {
      collections: '컬렉션',
      documents: '문서',
      chunks: '청크',
      documentsCount: '{{count}} 문서',
      chunksCount: '{{count}} 청크'
    },
    table: {
      collection: '컬렉션',
      stats: '통계',
      uuid: 'UUID',
      metadata: '메타데이터'
    },
    deleteConfirm: {
      title: '삭제 확인',
      description: '정말로 선택한 컬렉션을 삭제하시겠습니까? 이 작업은 복구할 수 없습니다.',
      collectionsToDelete: '삭제할 컬렉션 ({{count}}개):',
      warningMessage: '삭제된 컬렉션의 모든 문서도 함께 삭제됩니다.',
      deleteButton: '삭제',
      deleting: '삭제 중...',
      deleteSelected: '선택 항목 삭제'
    },
    popover: {
      basicInfo: '기본 정보',
      statistics: '통계'
    },
    messages: {
      fetchError: '컬렉션 조회 실패',
      deleteSuccess: '{{count}}개의 컬렉션이 성공적으로 삭제되었습니다.',
      deleteFailed: '{{count}}개의 컬렉션 삭제에 실패했습니다.'
    },
    modal: {
      createTitle: '새 컬렉션 만들기',
      nameLabel: '컬렉션 이름',
      namePlaceholder: '컬렉션 이름을 입력하세요',
      descriptionLabel: '설명',
      descriptionPlaceholder: '컬렉션 설명을 입력하세요 (선택사항)',
      creating: '생성 중...',
      createSuccess: '컬렉션이 성공적으로 생성되었습니다',
      createError: '컬렉션 생성 실패'
    }
  },
  documents: {
    title: '문서 관리',
    description: '컬렉션에 문서를 업로드하고 관리하세요',
    selectCollection: '먼저 컬렉션을 선택해주세요',
    uploadDocument: '문서 업로드',
    noDocuments: '문서가 없습니다',
    noDocumentsDescription: '이 컬렉션에 첫 번째 문서를 업로드하세요.',
    uploadFirstDocument: '첫 문서 업로드',
    table: {
      fileName: '파일명',
      uploadDate: '업로드 날짜',
      chunks: '청크',
      actions: '작업'
    },
    deleteConfirm: {
      title: '문서 삭제',
      description: '"{{fileName}}"을(를) 삭제하시겠습니까? 이 작업은 복구할 수 없습니다.',
      warningMessage: '이 문서와 관련된 모든 청크도 함께 삭제됩니다.'
    },
    messages: {
      uploadSuccess: '문서가 성공적으로 업로드되었습니다',
      uploadError: '문서 업로드 실패',
      deleteSuccess: '문서가 성공적으로 삭제되었습니다',
      deleteError: '문서 삭제 실패',
      fetchError: '문서 조회 실패'
    },
    modal: {
      uploadTitle: '문서 업로드',
      selectFile: '파일 선택',
      supportedFormats: '지원 형식: PDF, TXT, MD, DOCX, HTML',
      uploading: '업로드 중...',
      processing: '문서 처리 중...'
    }
  },
  search: {
    title: '문서 검색',
    description: '시맨틱 또는 키워드 검색을 사용하여 문서를 검색하세요',
    selectCollection: '컬렉션 선택',
    searchPlaceholder: '검색어를 입력하세요...',
    searchButton: '검색',
    searching: '검색 중...',
    searchType: '검색 유형',
    semanticSearch: '시맨틱 검색',
    keywordSearch: '키워드 검색',
    hybridSearch: '하이브리드 검색',
    alphaValue: '알파 값 (0-1)',
    noResults: '검색 결과가 없습니다',
    results: '검색 결과',
    relevanceScore: '관련도: {{score}}'
  },
  apiTester: {
    title: 'API 테스터',
    description: '인증을 사용하여 API 엔드포인트를 테스트하세요',
    endpoint: '엔드포인트',
    method: '메서드',
    headers: '헤더',
    body: '본문',
    sendRequest: '요청 보내기',
    response: '응답',
    responseTime: '응답 시간: {{time}}ms',
    status: '상태'
  },
  auth: {
    signIn: '로그인',
    signUp: '회원가입',
    email: '이메일',
    password: '비밀번호',
    confirmPassword: '비밀번호 확인',
    forgotPassword: '비밀번호를 잊으셨나요?',
    alreadyHaveAccount: '이미 계정이 있으신가요?',
    dontHaveAccount: '계정이 없으신가요?',
    signInError: '로그인 실패',
    signUpError: '회원가입 실패',
    logoutSuccess: '로그아웃되었습니다'
  },
  theme: {
    light: '라이트',
    dark: '다크',
    system: '시스템'
  },
  language: {
    english: 'English',
    korean: '한국어'
  }
}