package com.newspage.optimize.ui.navigation

import androidx.compose.runtime.*
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.newspage.optimize.ui.screens.login.LoginScreen
import com.newspage.optimize.ui.screens.dashboard.DashboardScreen
import com.newspage.optimize.ui.screens.inventory.InventoryScreen
import com.newspage.optimize.ui.screens.sales.SalesScreen
import com.newspage.optimize.ui.screens.promotion.PromotionScreen
import com.newspage.optimize.data.TokenManager

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Dashboard : Screen("dashboard")
    data object Inventory : Screen("inventory")
    data object Sales : Screen("sales")
    data object Promotion : Screen("promotion")
}

@Composable
fun AppNavigation(
    onSessionExpired: () -> Unit = {},
) {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = Screen.Login.route) {
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }
        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onNavigateToInventory = { navController.navigate(Screen.Inventory.route) },
                onNavigateToSales = { navController.navigate(Screen.Sales.route) },
                onNavigateToPromotion = { navController.navigate(Screen.Promotion.route) },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }
        composable(Screen.Inventory.route) {
            InventoryScreen(onBack = { navController.popBackStack() })
        }
        composable(Screen.Sales.route) {
            SalesScreen(onBack = { navController.popBackStack() })
        }
        composable(Screen.Promotion.route) {
            PromotionScreen(onBack = { navController.popBackStack() })
        }
    }
}
