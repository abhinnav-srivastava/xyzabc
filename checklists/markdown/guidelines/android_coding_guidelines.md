

**AND-001** (MUST): Use MVVM architecture pattern for UI components
  - **Good Example:**
```kotlin
class UserViewModel : ViewModel() {
    private val _user = MutableLiveData<User>()
    val user: LiveData<User> = _user
    
    fun loadUser(userId: String) {
        // Load user logic
    }
}
```
  - **Bad Example:**
```kotlin
class MainActivity : AppCompatActivity() {
    fun loadUser() {
        // Direct database access in Activity
        val user = database.getUser()
        textView.text = user.name
    }
}
```
  - **Measurement:** Code review checklist
  - **Reference:** Android Architecture Guide

**AND-002** (MUST): Implement Repository pattern for data access
  - **Good Example:**
```kotlin
class UserRepository @Inject constructor(
    private val localDataSource: UserLocalDataSource,
    private val remoteDataSource: UserRemoteDataSource
) {
    suspend fun getUser(id: String): Result<User> {
        return try {
            val user = remoteDataSource.getUser(id)
            localDataSource.saveUser(user)
            Result.success(user)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```
  - **Bad Example:**
```kotlin
class UserViewModel : ViewModel() {
    fun loadUser() {
        // Direct API calls in ViewModel
        apiService.getUser().enqueue(object : Callback<User> {
            // Handle response
        })
    }
}
```
  - **Measurement:** Architecture review
  - **Reference:** Android Architecture Components


**AND-003** (MUST): Implement proper exception handling
  - **Good Example:**
```kotlin
suspend fun fetchData(): Result<Data> {
    return try {
        val data = apiService.getData()
        Result.success(data)
    } catch (e: IOException) {
        Result.failure(NetworkException("Network error", e))
    } catch (e: Exception) {
        Result.failure(UnknownException("Unknown error", e))
    }
}
```
  - **Bad Example:**
```kotlin
fun fetchData() {
    try {
        val data = apiService.getData()
        // Handle success
    } catch (e: Exception) {
        // Generic exception handling
        Log.e("Error", e.message)
    }
}
```
  - **Measurement:** Code review
  - **Reference:** Android Error Handling Best Practices

**AND-004** (MUST): Use null safety features properly
  - **Good Example:**
```kotlin
fun processUser(user: User?) {
    user?.let {
        // Safe processing
        displayUser(it)
    } ?: run {
        // Handle null case
        showError("User not found")
    }
}
```
  - **Bad Example:**
```kotlin
fun processUser(user: User?) {
    if (user != null) {
        displayUser(user)
    }
    // Missing null handling
}
```
  - **Measurement:** Static analysis
  - **Reference:** Kotlin Null Safety Guide


**AND-005** (MUST): Write unit tests for business logic
  - **Good Example:**
```kotlin
@Test
fun `when user is valid, should return success`() {
    // Given
    val user = User("John", "john@example.com")
    
    // When
    val result = userValidator.validate(user)
    
    // Then
    assertTrue(result.isSuccess)
}
```
  - **Bad Example:**
```kotlin
// No unit tests written
class UserValidator {
    fun validate(user: User): Result<User> {
        // Validation logic without tests
    }
}
```
  - **Measurement:** Test coverage > 80%
  - **Reference:** Android Testing Guide

**AND-006** (GOOD): Write integration tests for critical flows
  - **Good Example:**
```kotlin
@RunWith(AndroidJUnit4::class)
class UserRepositoryIntegrationTest {
    @Test
    fun `should save and retrieve user from database`() {
        // Integration test implementation
    }
}
```
  - **Bad Example:**
```kotlin
// Only unit tests, no integration tests
```
  - **Measurement:** Critical path coverage
  - **Reference:** Android Testing Guide


**AND-007** (MUST): Avoid memory leaks in Activities and Fragments
  - **Good Example:**
```kotlin
class MainActivity : AppCompatActivity() {
    private val viewModel: MainViewModel by viewModels()
    
    override fun onDestroy() {
        super.onDestroy()
        // ViewModel automatically cleared
    }
}
```
  - **Bad Example:**
```kotlin
class MainActivity : AppCompatActivity() {
    private var listener: OnClickListener? = null
    
    override fun onDestroy() {
        super.onDestroy()
        // Memory leak - listener not cleared
    }
}
```
  - **Measurement:** Memory profiling
  - **Reference:** Android Memory Management

**AND-008** (MUST): Use appropriate threading mechanisms
  - **Good Example:**
```kotlin
class DataRepository {
    suspend fun fetchData(): Data = withContext(Dispatchers.IO) {
        // Background work
        apiService.getData()
    }
}
```
  - **Bad Example:**
```kotlin
class DataRepository {
    fun fetchData() {
        Thread {
            // Blocking main thread
            val data = apiService.getData()
            // Update UI on background thread
        }.start()
    }
}
```
  - **Measurement:** ANR detection
  - **Reference:** Android Threading Guide


**AND-009** (MUST): Encrypt sensitive data
  - **Good Example:**
```kotlin
class SecureStorage {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val encryptedPrefs = EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
}
```
  - **Bad Example:**
```kotlin
class InsecureStorage {
    private val prefs = context.getSharedPreferences("data", Context.MODE_PRIVATE)
    
    fun savePassword(password: String) {
        prefs.edit().putString("password", password).apply()
    }
}
```
  - **Measurement:** Security audit
  - **Reference:** Android Security Best Practices

**AND-010** (MUST): Use HTTPS for all network communications
  - **Good Example:**
```kotlin
class ApiClient {
    private val client = OkHttpClient.Builder()
        .certificatePinner(
            CertificatePinner.Builder()
                .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
                .build()
        )
        .build()
}
```
  - **Bad Example:**
```kotlin
class ApiClient {
    private val client = OkHttpClient.Builder()
        .build()
    // No certificate pinning
}
```
  - **Measurement:** Network security scan
  - **Reference:** Android Network Security Config


**AND-011** (MUST): Follow Kotlin naming conventions
  - **Good Example:**
```kotlin
class UserRepository {
    private val userDao: UserDao
    private val apiService: ApiService
    
    suspend fun getUserById(userId: String): User {
        // Implementation
    }
}
```
  - **Bad Example:**
```kotlin
class userRepository {
    private val UserDao: userDao
    private val API_SERVICE: ApiService
    
    suspend fun GetUserByID(user_id: String): User {
        // Implementation
    }
}
```
  - **Measurement:** Code review
  - **Reference:** Kotlin Coding Conventions

**AND-012** (GOOD): Use consistent code formatting
  - **Good Example:**
```kotlin
class DataProcessor {
    fun processData(
        input: List<String>,
        filter: (String) -> Boolean
    ): List<String> {
        return input
            .filter(filter)
            .map { it.trim() }
            .distinct()
    }
}
```
  - **Bad Example:**
```kotlin
class DataProcessor{
fun processData(input:List<String>,filter:(String)->Boolean):List<String>{
return input.filter(filter).map{it.trim()}.distinct()
}
}
```
  - **Measurement:** Automated formatting
  - **Reference:** Kotlin Style Guide


**AND-013** (MUST): Support different screen sizes
  - **Good Example:**
```xml
<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical">
    
    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textSize="@dimen/text_size_medium" />
</LinearLayout>
```
  - **Bad Example:**
```xml
<LinearLayout
    android:layout_width="300dp"
    android:layout_height="wrap_content"
    android:orientation="vertical">
    
    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textSize="16sp" />
</LinearLayout>
```
  - **Measurement:** UI testing on different devices
  - **Reference:** Android Responsive Design

**AND-014** (MUST): Implement accessibility features
  - **Good Example:**
```xml
<Button
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="@string/submit"
    android:contentDescription="@string/submit_button_description"
    android:importantForAccessibility="yes" />
```
  - **Bad Example:**
```xml
<Button
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Submit" />
```
  - **Measurement:** Accessibility testing
  - **Reference:** Android Accessibility Guide


**AND-015** (MUST): Use Retrofit for API calls
  - **Good Example:**
```kotlin
interface ApiService {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") userId: String): User
    
    @POST("users")
    suspend fun createUser(@Body user: User): Response<User>
}
```
  - **Bad Example:**
```kotlin
class ApiService {
    fun getUser(userId: String) {
        val url = "https://api.example.com/users/$userId"
        // Manual HTTP implementation
    }
}
```
  - **Measurement:** Code review
  - **Reference:** Retrofit Documentation

**AND-016** (MUST): Handle API errors gracefully
  - **Good Example:**
```kotlin
suspend fun fetchUser(userId: String): Result<User> {
    return try {
        val response = apiService.getUser(userId)
        if (response.isSuccessful) {
            Result.success(response.body()!!)
        } else {
            Result.failure(ApiException(response.code(), response.message()))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
}
```
  - **Bad Example:**
```kotlin
suspend fun fetchUser(userId: String): User {
    val response = apiService.getUser(userId)
    return response.body()!! // Potential crash
}
```
  - **Measurement:** Error monitoring
  - **Reference:** Android Error Handling


**AND-017** (GOOD): Implement proper logging
  - **Good Example:**
```kotlin
class UserRepository {
    private val logger = Logger.getLogger(UserRepository::class.java.name)
    
    suspend fun saveUser(user: User) {
        logger.info("Saving user: ${user.id}")
        try {
            userDao.insert(user)
            logger.info("User saved successfully: ${user.id}")
        } catch (e: Exception) {
            logger.error("Failed to save user: ${user.id}", e)
            throw e
        }
    }
}
```
  - **Bad Example:**
```kotlin
class UserRepository {
    suspend fun saveUser(user: User) {
        Log.d("User", "Saving user")
        userDao.insert(user)
        Log.d("User", "User saved")
    }
}
```
  - **Measurement:** Log analysis
  - **Reference:** Android Logging Best Practices


**AND-018** (MUST): Use Hilt for dependency injection
  - **Good Example:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    fun provideApiService(): ApiService {
        return Retrofit.Builder()
            .baseUrl("https://api.example.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
```
  - **Bad Example:**
```kotlin
class UserRepository {
    private val apiService = ApiService() // Direct instantiation
}
```
  - **Measurement:** Dependency analysis
  - **Reference:** Hilt Documentation


**AND-019** (MUST): Use coroutines for asynchronous operations
  - **Good Example:**
```kotlin
class UserViewModel : ViewModel() {
    private val _users = MutableLiveData<List<User>>()
    val users: LiveData<List<User>> = _users
    
    fun loadUsers() {
        viewModelScope.launch {
            try {
                val users = userRepository.getUsers()
                _users.value = users
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}
```
  - **Bad Example:**
```kotlin
class UserViewModel : ViewModel() {
    fun loadUsers() {
        Thread {
            val users = userRepository.getUsers()
            // Update UI on background thread - potential crash
        }.start()
    }
}
```
  - **Measurement:** Threading analysis
  - **Reference:** Kotlin Coroutines Guide

**AND-020** (GOOD): Use WorkManager for background tasks
  - **Good Example:**
```kotlin
@HiltWorker
class DataSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val repository: DataRepository
) : CoroutineWorker(context, workerParams) {
    
    override suspend fun doWork(): Result {
        return try {
            repository.syncData()
            Result.success()
        } catch (e: Exception) {
            Result.failure()
        }
    }
}
```
  - **Bad Example:**
```kotlin
class DataSyncService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Manual background processing
        return START_STICKY
    }
}
```
  - **Measurement:** Background task monitoring
  - **Reference:** WorkManager Guide


**AND-021** (MUST): Use Room for local database operations
  - **Good Example:**
```kotlin
@Entity(tableName = "users")
data class User(
    @PrimaryKey val id: String,
    val name: String,
    val email: String
)

@Dao
interface UserDao {
    @Query("SELECT * FROM users")
    suspend fun getAllUsers(): List<User>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: User)
}
```
  - **Bad Example:**
```kotlin
class UserDatabase {
    fun saveUser(user: User) {
        // Manual SQLite implementation
        val db = writableDatabase
        val values = ContentValues()
        values.put("id", user.id)
        values.put("name", user.name)
        db.insert("users", null, values)
    }
}
```
  - **Measurement:** Database performance
  - **Reference:** Room Documentation

**AND-022** (GOOD): Use DataStore instead of SharedPreferences
  - **Good Example:**
```kotlin
class UserPreferencesRepository @Inject constructor(
    private val dataStore: DataStore<Preferences>
) {
    val userTheme: Flow<String> = dataStore.data
        .map { preferences ->
            preferences[USER_THEME] ?: "system"
        }
    
    suspend fun updateTheme(theme: String) {
        dataStore.edit { preferences ->
            preferences[USER_THEME] = theme
        }
    }
}
```
  - **Bad Example:**
```kotlin
class UserPreferences {
    private val prefs = context.getSharedPreferences("user_prefs", Context.MODE_PRIVATE)
    
    fun saveTheme(theme: String) {
        prefs.edit().putString("theme", theme).apply()
    }
}
```
  - **Measurement:** Preference usage analysis
  - **Reference:** DataStore Documentation


**AND-023** (GOOD): Write clear commit messages
  - **Good Example:**
```
feat: add user authentication with biometric login

- Implement BiometricPrompt for secure authentication
- Add fallback to PIN/password authentication
- Update login flow to support multiple auth methods

Closes #123
```
  - **Bad Example:**
```
fix stuff
```
  - **Measurement:** Commit message analysis
  - **Reference:** Conventional Commits

**AND-024** (GOOD): Use feature branches for development
  - **Good Example:**
```
feature/user-authentication
bugfix/login-crash-fix
hotfix/security-patch
```
  - **Bad Example:**
```
working-on-login
test
fix
```
  - **Measurement:** Branch naming analysis
  - **Reference:** Git Flow Guide

