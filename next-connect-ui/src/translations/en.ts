export const en = {
  common: {
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    search: 'Search',
    refresh: 'Refresh',
    logout: 'Log out',
    none: 'None',
    selectAll: 'Select all',
    selected: '{{count}} selected',
    total: 'Total {{count}}',
  },
  sidebar: {
    main: 'Main',
    collections: 'Collections',
    documents: 'Documents',
    search: 'Search',
    apiTester: 'API Tester',
    mainTitle: 'Main'
  },
  collections: {
    title: 'Collection Management',
    description: 'Create and manage document collections',
    newCollection: 'New Collection',
    collectionList: 'Collection List',
    noCollections: 'No collections',
    noCollectionsDescription: 'Create your first collection to organize documents systematically.',
    createFirstCollection: 'Create First Collection',
    stats: {
      collections: 'Collections',
      documents: 'Documents',
      chunks: 'Chunks',
      documentsCount: '{{count}} documents',
      chunksCount: '{{count}} chunks'
    },
    table: {
      collection: 'Collection',
      stats: 'Statistics',
      uuid: 'UUID',
      metadata: 'Metadata'
    },
    deleteConfirm: {
      title: 'Delete Confirmation',
      description: 'Are you sure you want to delete the selected collections? This action cannot be undone.',
      collectionsToDelete: 'Collections to delete ({{count}}):',
      warningMessage: 'All documents in the deleted collections will also be deleted.',
      deleteButton: 'Delete',
      deleting: 'Deleting...',
      deleteSelected: 'Delete Selected'
    },
    popover: {
      basicInfo: 'Basic Information',
      statistics: 'Statistics'
    },
    messages: {
      fetchError: 'Failed to fetch collections',
      deleteSuccess: '{{count}} collections successfully deleted.',
      deleteFailed: '{{count}} collections failed to delete.'
    },
    modal: {
      createTitle: 'Create New Collection',
      nameLabel: 'Collection Name',
      namePlaceholder: 'Enter collection name',
      descriptionLabel: 'Description',
      descriptionPlaceholder: 'Enter collection description (optional)',
      creating: 'Creating...',
      createSuccess: 'Collection created successfully',
      createError: 'Failed to create collection'
    }
  },
  documents: {
    title: 'Document Management',
    description: 'Upload and manage documents in collections',
    selectCollection: 'Please select a collection first',
    uploadDocument: 'Upload Document',
    noDocuments: 'No documents',
    noDocumentsDescription: 'Upload your first document to this collection.',
    uploadFirstDocument: 'Upload First Document',
    table: {
      fileName: 'File Name',
      uploadDate: 'Upload Date',
      chunks: 'Chunks',
      actions: 'Actions'
    },
    deleteConfirm: {
      title: 'Delete Document',
      description: 'Are you sure you want to delete "{{fileName}}"? This action cannot be undone.',
      warningMessage: 'All chunks associated with this document will also be deleted.'
    },
    messages: {
      uploadSuccess: 'Document uploaded successfully',
      uploadError: 'Failed to upload document',
      deleteSuccess: 'Document deleted successfully',
      deleteError: 'Failed to delete document',
      fetchError: 'Failed to fetch documents'
    },
    modal: {
      uploadTitle: 'Upload Document',
      selectFile: 'Select File',
      supportedFormats: 'Supported formats: PDF, TXT, MD, DOCX, HTML',
      uploading: 'Uploading...',
      processing: 'Processing document...'
    }
  },
  search: {
    title: 'Document Search',
    description: 'Search documents using semantic or keyword search',
    selectCollection: 'Select Collection',
    searchPlaceholder: 'Enter search query...',
    searchButton: 'Search',
    searching: 'Searching...',
    searchType: 'Search Type',
    semanticSearch: 'Semantic Search',
    keywordSearch: 'Keyword Search',
    hybridSearch: 'Hybrid Search',
    alphaValue: 'Alpha value (0-1)',
    noResults: 'No results found',
    results: 'Search Results',
    relevanceScore: 'Relevance: {{score}}'
  },
  apiTester: {
    title: 'API Tester',
    description: 'Test API endpoints with authentication',
    endpoint: 'Endpoint',
    method: 'Method',
    headers: 'Headers',
    body: 'Body',
    sendRequest: 'Send Request',
    response: 'Response',
    responseTime: 'Response time: {{time}}ms',
    status: 'Status'
  },
  auth: {
    signIn: 'Sign In',
    signUp: 'Sign Up',
    email: 'Email',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    forgotPassword: 'Forgot Password?',
    alreadyHaveAccount: 'Already have an account?',
    dontHaveAccount: "Don't have an account?",
    signInError: 'Failed to sign in',
    signUpError: 'Failed to sign up',
    logoutSuccess: 'Logged out successfully'
  },
  theme: {
    light: 'Light',
    dark: 'Dark',
    system: 'System'
  },
  language: {
    english: 'English',
    korean: '한국어'
  }
}