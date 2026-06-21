package com.newspage.optimize.data

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.http.*

interface OptimizeApi {
    // Auth
    @POST("api/auth/login")
    suspend fun login(@Body body: Map<String, String>): retrofit2.Response<Map<String, Any>>

    @POST("api/auth/refresh")
    suspend fun refreshToken(@Body body: Map<String, String>): retrofit2.Response<Map<String, Any>>

    @GET("api/auth/me")
    suspend fun getMe(): retrofit2.Response<Map<String, Any>>

    // Health
    @GET("api/health")
    suspend fun healthCheck(): retrofit2.Response<Map<String, Any>>

    // Dashboard
    @GET("api/dashboard/")
    suspend fun getDashboard(): retrofit2.Response<Map<String, Any>>

    // Distributors
    @GET("api/distributors/")
    suspend fun getDistributors(): retrofit2.Response<Map<String, Any>>

    @GET("api/distributors/{name}/credentials")
    suspend fun getCredentials(@Path("name") name: String): retrofit2.Response<Map<String, Any>>

    // Inventory
    @Multipart
    @POST("api/inventory/extract")
    suspend fun extractInventory(
        @Part("distributor") distributor: RequestBody,
        @Part("np_user_id") npUserId: RequestBody,
        @Part("np_password") npPassword: RequestBody,
    ): retrofit2.Response<Map<String, Any>>

    @Multipart
    @POST("api/inventory/compare")
    suspend fun compareInventory(
        @Part("job_id") jobId: RequestBody,
        @Part distFile: MultipartBody.Part,
        @Part("sku_col_np") skuColNp: RequestBody,
        @Part("desc_col_np") descColNp: RequestBody,
        @Part("qty_col_np") qtyColNp: RequestBody,
        @Part("sku_col_dist") skuColDist: RequestBody,
        @Part("qty_col_dist") qtyColDist: RequestBody,
    ): retrofit2.Response<Map<String, Any>>

    @Multipart
    @POST("api/inventory/execute")
    suspend fun executeAdjustment(
        @Part("job_id") jobId: RequestBody,
        @Part("np_user_id") npUserId: RequestBody,
        @Part("np_password") npPassword: RequestBody,
    ): retrofit2.Response<Map<String, Any>>

    // Sales
    @Multipart
    @POST("api/sales/extract")
    suspend fun extractSales(
        @Part("distributor") distributor: RequestBody,
        @Part("np_user_id") npUserId: RequestBody,
        @Part("np_password") npPassword: RequestBody,
        @Part("start_date") startDate: RequestBody,
        @Part("end_date") endDate: RequestBody,
    ): retrofit2.Response<Map<String, Any>>

    // Promotion
    @Multipart
    @POST("api/promotion/sync")
    suspend fun syncPromotion(
        @Part("start_date") startDate: RequestBody,
        @Part("end_date") endDate: RequestBody,
    ): retrofit2.Response<Map<String, Any>>

    @Multipart
    @POST("api/promotion/compare")
    suspend fun comparePromotion(
        @Part("job_id") jobId: RequestBody,
        @Part sharepointFile: MultipartBody.Part,
        @Part("filter_status") filterStatus: RequestBody,
    ): retrofit2.Response<Map<String, Any>>

    // Downloads (raw bytes)
    @Streaming
    @GET("api/sales/download/{job_id}")
    suspend fun downloadSales(@Path("job_id") jobId: String): retrofit2.Response<okhttp3.ResponseBody>

    @Streaming
    @GET("api/promotion/download/{job_id}")
    suspend fun downloadPromotion(@Path("job_id") jobId: String): retrofit2.Response<okhttp3.ResponseBody>

    @Streaming
    @GET("api/promotion/download/{job_id}/comparison")
    suspend fun downloadComparison(@Path("job_id") jobId: String): retrofit2.Response<okhttp3.ResponseBody>

    @Streaming
    @GET("api/download/{job_id}")
    suspend fun downloadGeneric(@Path("job_id") jobId: String): retrofit2.Response<okhttp3.ResponseBody>
}
