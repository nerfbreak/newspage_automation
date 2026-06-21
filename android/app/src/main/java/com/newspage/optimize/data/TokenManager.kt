package com.newspage.optimize.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "auth")

class TokenManager(private val context: Context) {
    private val accessTokenKey = stringPreferencesKey("access_token")
    private val refreshTokenKey = stringPreferencesKey("refresh_token")
    private val usernameKey = stringPreferencesKey("username")

    suspend fun saveTokens(accessToken: String, refreshToken: String, username: String) {
        context.dataStore.edit { prefs ->
            prefs[accessTokenKey] = accessToken
            prefs[refreshTokenKey] = refreshToken
            prefs[usernameKey] = username
        }
    }

    suspend fun getAccessToken(): String? =
        context.dataStore.data.map { it[accessTokenKey] }.first()

    suspend fun getRefreshToken(): String? =
        context.dataStore.data.map { it[refreshTokenKey] }.first()

    suspend fun getUsername(): String? =
        context.dataStore.data.map { it[usernameKey] }.first()

    suspend fun clear() {
        context.dataStore.edit { it.clear() }
    }
}
