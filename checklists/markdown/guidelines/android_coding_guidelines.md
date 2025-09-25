# Android Coding Guidelines

## Style

### Naming

**AND-001** (MUST): Use PascalCase for class names

  - **Good Example:**
```kotlin
public class UserProfileActivity
```
  - **Bad Example:**
```kotlin
public class userProfileActivity
```
  - **Measurement:** Android Code Style Guide
  - **Reference:** https://developer.android.com/kotlin/style-guide

### Formatting

**AND-002** (MUST): Use 4 spaces for indentation

  - **Good Example:**
```kotlin
if (condition) {
    doSomething();
}
```
  - **Bad Example:**
```kotlin
if (condition) {
  doSomething();
}
```
  - **Measurement:** IDE formatting rules
  - **Reference:** https://developer.android.com/kotlin/style-guide

### Documentation

**AND-003** (GOOD): Add KDoc for public APIs

  - **Good Example:**
```kotlin
/**
 * Retrieves user profile
 */
```
  - **Bad Example:**
```kotlin
// Gets user data
```
  - **Measurement:** KDoc coverage reports
  - **Reference:** https://kotlinlang.org/docs/kotlin-doc.html

### Variables

**AND-004** (GOOD): Use val for immutable variables

  - **Good Example:**
```kotlin
val userName = "John"
```
  - **Bad Example:**
```kotlin
var userName = "John"
```
  - **Measurement:** IDE variable warnings
  - **Reference:** https://kotlinlang.org/docs/basic-syntax.html

## Error Handling

### Exceptions

**AND-005** (MUST): Use specific exception types

  - **Good Example:**
```kotlin
throw IllegalArgumentException("Invalid ID")
```
  - **Bad Example:**
```kotlin
throw Exception("Error occurred")
```
  - **Measurement:** Exception handling audit
  - **Reference:** https://kotlinlang.org/docs/exceptions.html

### Try-Catch

**AND-006** (MUST): Handle exceptions at appropriate levels

  - **Good Example:**
```kotlin
try { riskyOperation() } catch (e: IOException) { handleError(e) }
```
  - **Bad Example:**
```kotlin
val result = riskyOperation() // No error handling
```
  - **Measurement:** Code coverage analysis
  - **Reference:** https://kotlinlang.org/docs/exceptions.html

### User Feedback

**AND-007** (MUST): Show user-friendly error messages

  - **Good Example:**
```kotlin
showError("Unable to connect to server")
```
  - **Bad Example:**
```kotlin
showError("IOException: Connection refused")
```
  - **Measurement:** User feedback analysis
  - **Reference:** https://material.io/design/communication/errors.html

### Monitoring

**AND-008** (MUST): Report errors to crash reporting service

  - **Good Example:**
```kotlin
FirebaseCrashlytics.getInstance().recordException(exception)
```
  - **Bad Example:**
```kotlin
Log.e(TAG, "Error occurred", exception)
```
  - **Measurement:** Crash reporting dashboard
  - **Reference:** https://firebase.google.com/docs/crashlytics

## DI

### Hilt Setup

**AND-009** (GOOD): Use Hilt for dependency injection

  - **Good Example:**
```kotlin
@HiltAndroidApp
class MyApplication : Application()
```
  - **Bad Example:**
```kotlin
Manual dependency creation in activities
```
  - **Measurement:** DI framework adoption
  - **Reference:** https://developer.android.com/training/dependency-injection/hilt-android

### Modules

**AND-010** (GOOD): Organize dependencies in modules

  - **Good Example:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule
```
  - **Bad Example:**
```kotlin
All dependencies in Application class
```
  - **Measurement:** Module organization review
  - **Reference:** https://developer.android.com/training/dependency-injection/hilt-android

### Scopes

**AND-011** (GOOD): Use appropriate scopes for dependencies

  - **Good Example:**
```kotlin
@Singleton
class UserRepository
```
  - **Bad Example:**
```kotlin
No scope annotations
```
  - **Measurement:** Scope usage analysis
  - **Reference:** https://developer.android.com/training/dependency-injection/hilt-android

### Testing

**AND-012** (GOOD): Use test modules for unit testing

  - **Good Example:**
```kotlin
@TestInstallIn
@Module
object TestDatabaseModule
```
  - **Bad Example:**
```kotlin
Using production dependencies in tests
```
  - **Measurement:** Test isolation verification
  - **Reference:** https://developer.android.com/training/dependency-injection/hilt-android

## Performance

### Memory

**AND-013** (MUST): Avoid memory leaks by managing listeners

  - **Good Example:**
```kotlin
removeListener() in onDestroy()
```
  - **Bad Example:**
```kotlin
Forgetting to remove listeners
```
  - **Measurement:** LeakCanary detection
  - **Reference:** https://square.github.io/leakcanary/

### Images

**AND-014** (MUST): Use appropriate image loading library

  - **Good Example:**
```kotlin
Glide.with(context).load(url).into(imageView)
```
  - **Bad Example:**
```kotlin
Loading images on main thread
```
  - **Measurement:** Memory profiling tools
  - **Reference:** https://bumptech.github.io/glide/

### Lists

**AND-015** (MUST): Use ViewHolder pattern for RecyclerView

  - **Good Example:**
```kotlin
class MyViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView)
```
  - **Bad Example:**
```kotlin
findViewById in onBindViewHolder
```
  - **Measurement:** UI performance metrics
  - **Reference:** https://developer.android.com/guide/topics/ui/layout/recyclerview

### Background

**AND-016** (MUST): Use background threads for heavy operations

  - **Good Example:**
```kotlin
lifecycleScope.launch(Dispatchers.IO) { heavyOperation() }
```
  - **Bad Example:**
```kotlin
heavyOperation() on main thread
```
  - **Measurement:** ANR detection tools
  - **Reference:** https://developer.android.com/kotlin/coroutines

## Logging

### Levels

**AND-017** (MUST): Use appropriate log levels

  - **Good Example:**
```kotlin
Log.d(TAG, "Debug info"), Log.e(TAG, "Error", exception)
```
  - **Bad Example:**
```kotlin
Log.d(TAG, "Error occurred")
```
  - **Measurement:** Log analysis tools
  - **Reference:** https://developer.android.com/reference/android/util/Log

### Tags

**AND-018** (GOOD): Use consistent TAG naming

  - **Good Example:**
```kotlin
companion object { private const val TAG = "UserProfileActivity" }
```
  - **Bad Example:**
```kotlin
Log.d("TAG", "message")
```
  - **Measurement:** Log filtering analysis
  - **Reference:** https://developer.android.com/reference/android/util/Log

### Production

**AND-019** (MUST): Remove debug logs in production

  - **Good Example:**
```kotlin
if (BuildConfig.DEBUG) Log.d(TAG, message)
```
  - **Bad Example:**
```kotlin
Log.d(TAG, "Sensitive data: $password")
```
  - **Measurement:** Build configuration review
  - **Reference:** https://developer.android.com/studio/build/build-variants

## Threading

### Main Thread

**AND-020** (MUST): Keep main thread free for UI operations

  - **Good Example:**
```kotlin
lifecycleScope.launch { updateUI() }
```
  - **Bad Example:**
```kotlin
Thread.sleep(1000) on main thread
```
  - **Measurement:** ANR detection tools
  - **Reference:** https://developer.android.com/kotlin/coroutines

### Coroutines

**AND-021** (GOOD): Use coroutines instead of threads

  - **Good Example:**
```kotlin
lifecycleScope.launch(Dispatchers.IO) { apiCall() }
```
  - **Bad Example:**
```kotlin
Thread { apiCall() }.start()
```
  - **Measurement:** Thread usage analysis
  - **Reference:** https://developer.android.com/kotlin/coroutines

### Scope

**AND-022** (GOOD): Use appropriate coroutine scope

  - **Good Example:**
```kotlin
viewModelScope.launch { fetchData() }
```
  - **Bad Example:**
```kotlin
GlobalScope.launch { fetchData() }
```
  - **Measurement:** Scope usage review
  - **Reference:** https://developer.android.com/kotlin/coroutines

## API Usage

### Retrofit

**AND-023** (GOOD): Use Retrofit for network calls

  - **Good Example:**
```kotlin
@GET("users/{id}") suspend fun getUser(@Path("id") id: Int): User
```
  - **Bad Example:**
```kotlin
Manual HTTP requests with HttpURLConnection
```
  - **Measurement:** Network library adoption
  - **Reference:** https://square.github.io/retrofit/

### Error Handling

**AND-024** (MUST): Handle API errors properly

  - **Good Example:**
```kotlin
try { response = api.getData() } catch (e: HttpException) { handleError(e) }
```
  - **Bad Example:**
```kotlin
val data = api.getData() // No error handling
```
  - **Measurement:** API error monitoring
  - **Reference:** https://square.github.io/retrofit/

### Caching

**AND-025** (GOOD): Implement proper caching strategy

  - **Good Example:**
```kotlin
@Headers("Cache-Control: max-age=300")
```
  - **Bad Example:**
```kotlin
No caching headers or strategy
```
  - **Measurement:** Network performance metrics
  - **Reference:** https://square.github.io/okhttp/

### Pagination

**AND-026** (GOOD): Handle paginated API responses

  - **Good Example:**
```kotlin
data class ApiResponse<T>(val data: List<T>, val nextPage: String?)
```
  - **Bad Example:**
```kotlin
Loading all data at once
```
  - **Measurement:** API response size analysis
  - **Reference:** https://developer.android.com/topic/architecture/data-layer

## Security

### Data Storage

**AND-027** (MUST): Use Android Keystore for sensitive data

  - **Good Example:**
```kotlin
EncryptedSharedPreferences.create("secret_prefs")
```
  - **Bad Example:**
```kotlin
Storing passwords in plain SharedPreferences
```
  - **Measurement:** Security audit tools
  - **Reference:** https://developer.android.com/topic/security/best-practices

### Network

**AND-028** (MUST): Use HTTPS for all network communications

  - **Good Example:**
```kotlin
https://api.example.com/users
```
  - **Bad Example:**
```kotlin
http://api.example.com/users
```
  - **Measurement:** Network security scanner
  - **Reference:** https://developer.android.com/topic/security/best-practices

### Input Validation

**AND-029** (MUST): Validate all user inputs

  - **Good Example:**
```kotlin
if (email.isValidEmail()) processEmail(email)
```
  - **Bad Example:**
```kotlin
processEmail(email) // No validation
```
  - **Measurement:** Input validation tests
  - **Reference:** https://developer.android.com/topic/security/best-practices

### Logging

**AND-030** (MUST): Never log sensitive information

  - **Good Example:**
```kotlin
Log.d(TAG, "User login successful")
```
  - **Bad Example:**
```kotlin
Log.d(TAG, "Password: $password")
```
  - **Measurement:** Log security audit
  - **Reference:** https://developer.android.com/topic/security/best-practices

## Git

### Commits

**AND-031** (GOOD): Write clear commit messages

  - **Good Example:**
```kotlin
feat: add user profile validation
```
  - **Bad Example:**
```kotlin
fix stuff
```
  - **Measurement:** Commit message analysis
  - **Reference:** https://www.conventionalcommits.org/

### Branching

**AND-032** (GOOD): Use feature branches for development

  - **Good Example:**
```kotlin
feature/user-authentication
```
  - **Bad Example:**
```kotlin
Committing directly to main branch
```
  - **Measurement:** Branch strategy review
  - **Reference:** https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows

### Pull Requests

**AND-033** (GOOD): Create pull requests for code review

  - **Good Example:**
```kotlin
PR with clear description and tests
```
  - **Bad Example:**
```kotlin
Direct merge without review
```
  - **Measurement:** PR review metrics
  - **Reference:** https://docs.github.com/en/pull-requests

## UI/UX

### Material Design

**AND-034** (GOOD): Follow Material Design guidelines

  - **Good Example:**
```kotlin
Using Material Design components and themes
```
  - **Bad Example:**
```kotlin
Custom UI that doesn't follow guidelines
```
  - **Measurement:** Design system compliance
  - **Reference:** https://material.io/design

### Accessibility

**AND-035** (MUST): Add accessibility labels and content descriptions

  - **Good Example:**
```kotlin
android:contentDescription="Save button"
```
  - **Bad Example:**
```kotlin
No accessibility labels
```
  - **Measurement:** Accessibility testing tools
  - **Reference:** https://developer.android.com/guide/topics/ui/accessibility

### Responsive

**AND-036** (GOOD): Design for different screen sizes

  - **Good Example:**
```kotlin
Using ConstraintLayout with proper constraints
```
  - **Bad Example:**
```kotlin
Fixed pixel values for all dimensions
```
  - **Measurement:** Multi-device testing
  - **Reference:** https://material.io/design/layout/responsive-layout-grid.html

### Loading States

**AND-037** (GOOD): Show loading states for async operations

  - **Good Example:**
```kotlin
ProgressBar while loading data
```
  - **Bad Example:**
```kotlin
Blank screen during loading
```
  - **Measurement:** User experience metrics
  - **Reference:** https://material.io/design/communication/loading.html

## Architecture

### MVVM

**AND-038** (GOOD): Follow MVVM architecture pattern

  - **Good Example:**
```kotlin
ViewModel handles business logic, View observes LiveData
```
  - **Bad Example:**
```kotlin
Business logic mixed in Activity
```
  - **Measurement:** Architecture review
  - **Reference:** https://developer.android.com/jetpack/guide

### Repository

**AND-039** (GOOD): Use Repository pattern for data access

  - **Good Example:**
```kotlin
class UserRepository(private val api: UserApi, private val db: UserDao)
```
  - **Bad Example:**
```kotlin
Direct API calls from ViewModels
```
  - **Measurement:** Architecture components usage
  - **Reference:** https://developer.android.com/jetpack/guide

### Separation

**AND-040** (MUST): Separate concerns properly

  - **Good Example:**
```kotlin
UI logic in View, business logic in ViewModel
```
  - **Bad Example:**
```kotlin
All logic in Activity
```
  - **Measurement:** Code organization review
  - **Reference:** https://developer.android.com/jetpack/guide

### Data Flow

**AND-041** (GOOD): Use unidirectional data flow

  - **Good Example:**
```kotlin
View -> ViewModel -> Repository -> API
```
  - **Bad Example:**
```kotlin
Circular dependencies between components
```
  - **Measurement:** Data flow analysis
  - **Reference:** https://developer.android.com/jetpack/guide

## Permissions

### Runtime

**AND-042** (MUST): Request permissions at runtime

  - **Good Example:**
```kotlin
requestPermissions(arrayOf(CAMERA), REQUEST_CODE)
```
  - **Bad Example:**
```kotlin
Assuming permissions are granted
```
  - **Measurement:** Permission usage analysis
  - **Reference:** https://developer.android.com/training/permissions/requesting

### Rationale

**AND-043** (GOOD): Show rationale for permission requests

  - **Good Example:**
```kotlin
Explaining why camera access is needed
```
  - **Bad Example:**
```kotlin
Requesting permission without explanation
```
  - **Measurement:** User permission grant rate
  - **Reference:** https://developer.android.com/training/permissions/requesting

### Minimal

**AND-044** (MUST): Request only necessary permissions

  - **Good Example:**
```kotlin
Only CAMERA permission for camera feature
```
  - **Bad Example:**
```kotlin
Requesting all permissions upfront
```
  - **Measurement:** Permission audit
  - **Reference:** https://developer.android.com/training/permissions/requesting

## License

### Dependencies

**AND-045** (MUST): Include license information for dependencies

  - **Good Example:**
```kotlin
License report in build output
```
  - **Bad Example:**
```kotlin
No license tracking
```
  - **Measurement:** License compliance audit
  - **Reference:** https://developer.android.com/studio/build/manage-dependencies

### Attribution

**AND-046** (MUST): Provide proper attribution for open source libraries

  - **Good Example:**
```kotlin
About screen with library credits
```
  - **Bad Example:**
```kotlin
No attribution for used libraries
```
  - **Measurement:** Attribution compliance check
  - **Reference:** https://developer.android.com/studio/build/manage-dependencies

### Compatibility

**AND-047** (MUST): Ensure license compatibility

  - **Good Example:**
```kotlin
Using MIT/Apache licensed libraries
```
  - **Bad Example:**
```kotlin
Mixing incompatible licenses
```
  - **Measurement:** License compatibility analysis
  - **Reference:** https://developer.android.com/studio/build/manage-dependencies

## Storage

### Database

**AND-048** (GOOD): Use Room for local database operations

  - **Good Example:**
```kotlin
@Entity
@Dao
class UserDao
```
  - **Bad Example:**
```kotlin
Raw SQL queries in code
```
  - **Measurement:** Database library adoption
  - **Reference:** https://developer.android.com/training/data-storage/room

### Preferences

**AND-049** (GOOD): Use DataStore for preferences

  - **Good Example:**
```kotlin
val userPreferences = DataStore(PreferencesDataStoreFactory.create())
```
  - **Bad Example:**
```kotlin
SharedPreferences for complex data
```
  - **Measurement:** Preferences usage analysis
  - **Reference:** https://developer.android.com/topic/libraries/architecture/datastore

### Files

**AND-050** (MUST): Store files in appropriate directories

  - **Good Example:**
```kotlin
context.getExternalFilesDir(Environment.DIRECTORY_PICTURES)
```
  - **Bad Example:**
```kotlin
Storing files in root directory
```
  - **Measurement:** File storage audit
  - **Reference:** https://developer.android.com/training/data-storage

### Cache

**AND-051** (GOOD): Implement proper cache management

  - **Good Example:**
```kotlin
Cache with TTL and size limits
```
  - **Bad Example:**
```kotlin
Unlimited cache growth
```
  - **Measurement:** Cache performance metrics
  - **Reference:** https://developer.android.com/topic/architecture/data-layer

## Logic

### Business Rules

**AND-052** (GOOD): Centralize business logic in appropriate layers

  - **Good Example:**
```kotlin
Business logic in UseCase classes
```
  - **Bad Example:**
```kotlin
Business logic scattered in UI
```
  - **Measurement:** Logic organization review
  - **Reference:** https://developer.android.com/jetpack/guide

### Validation

**AND-053** (MUST): Validate data at multiple layers

  - **Good Example:**
```kotlin
Input validation in UI, business validation in UseCase
```
  - **Bad Example:**
```kotlin
No validation or validation in one place only
```
  - **Measurement:** Validation coverage analysis
  - **Reference:** https://developer.android.com/jetpack/guide

### State

**AND-054** (GOOD): Manage state consistently

  - **Good Example:**
```kotlin
Single source of truth for state
```
  - **Bad Example:**
```kotlin
State scattered across multiple variables
```
  - **Measurement:** State management review
  - **Reference:** https://developer.android.com/jetpack/compose/state

## CodeStyle

### Functions

**AND-055** (GOOD): Keep functions small and focused

  - **Good Example:**
```kotlin
fun validateEmail(email: String): Boolean
```
  - **Bad Example:**
```kotlin
fun processUserDataAndSendEmailAndUpdateDatabase()
```
  - **Measurement:** Function complexity analysis
  - **Reference:** https://developer.android.com/kotlin/style-guide

### Classes

**AND-056** (GOOD): Follow Single Responsibility Principle

  - **Good Example:**
```kotlin
class EmailValidator, class UserRepository
```
  - **Bad Example:**
```kotlin
class UserManager (handles validation, storage, networking)
```
  - **Measurement:** Class responsibility analysis
  - **Reference:** https://developer.android.com/kotlin/style-guide

### Constants

**AND-057** (GOOD): Use constants for magic numbers and strings

  - **Good Example:**
```kotlin
companion object { private const val MAX_RETRY_COUNT = 3 }
```
  - **Bad Example:**
```kotlin
if (retryCount < 3) // Magic number
```
  - **Measurement:** Magic number detection
  - **Reference:** https://developer.android.com/kotlin/style-guide

### Readability

**AND-058** (GOOD): Write self-documenting code

  - **Good Example:**
```kotlin
val isValidUser = user.isActive && user.hasPermission
```
  - **Bad Example:**
```kotlin
val flag = user.flag1 && user.flag2
```
  - **Measurement:** Code readability metrics
  - **Reference:** https://developer.android.com/kotlin/style-guide

## Testing

### Unit Tests

**AND-059** (GOOD): Write unit tests for business logic

  - **Good Example:**
```kotlin
@Test fun validateEmail_returnsTrue_forValidEmail()
```
  - **Bad Example:**
```kotlin
No unit tests for critical logic
```
  - **Measurement:** Test coverage reports
  - **Reference:** https://developer.android.com/training/testing/unit-testing

### Integration

**AND-060** (GOOD): Write integration tests for data layer

  - **Good Example:**
```kotlin
@RunWith(AndroidJUnit4::class)
class UserDaoTest
```
  - **Bad Example:**
```kotlin
Only unit tests, no integration tests
```
  - **Measurement:** Integration test coverage
  - **Reference:** https://developer.android.com/training/testing/integration-tests

### UI Tests

**AND-061** (GOOD): Write UI tests for critical user flows

  - **Good Example:**
```kotlin
@Test fun login_withValidCredentials_opensHomeScreen()
```
  - **Bad Example:**
```kotlin
No UI tests for user flows
```
  - **Measurement:** UI test coverage
  - **Reference:** https://developer.android.com/training/testing/ui-tests

### Mocking

**AND-062** (GOOD): Use proper mocking for dependencies

  - **Good Example:**
```kotlin
@Mock lateinit var userRepository: UserRepository
```
  - **Bad Example:**
```kotlin
Using real dependencies in tests
```
  - **Measurement:** Test isolation analysis
  - **Reference:** https://developer.android.com/training/testing/unit-testing

