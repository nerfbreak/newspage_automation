package com.newspage.optimize.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.newspage.optimize.ui.theme.BrandBlue
import com.newspage.optimize.ui.theme.BrandSurface
import com.newspage.optimize.ui.theme.BrandTextMuted

@Composable
fun MetricCard(
    title: String,
    value: String,
    modifier: Modifier = Modifier,
    accent: Boolean = false,
) {
    val bg = if (accent) BrandBlue else BrandSurface
    val fg = if (accent) Color.White else MaterialTheme.colorScheme.onBackground
    val border = if (accent) Color(0x26006AC9) else Color(0x14000000)

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(125.dp)
            .background(bg, RoundedCornerShape(10.dp))
            .border(1.dp, border, RoundedCornerShape(10.dp))
            .padding(20.dp),
    ) {
        Column {
            Text(
                text = title,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                color = if (accent) Color.White.copy(alpha = 0.7f) else BrandTextMuted,
            )
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = value,
                fontSize = if (value.length > 10) 18.sp else 32.sp,
                fontWeight = FontWeight.Bold,
                color = fg,
            )
        }
    }
}

@Composable
fun StatusPill(
    label: String,
    status: String,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Color.White, RoundedCornerShape(10.dp))
            .border(1.dp, Color(0x0F000000), RoundedCornerShape(10.dp))
            .padding(horizontal = 18.dp, vertical = 16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
        Box(
            modifier = Modifier
                .background(color.copy(alpha = 0.1f), RoundedCornerShape(20.dp))
                .border(1.dp, color.copy(alpha = 0.2f), RoundedCornerShape(20.dp))
                .padding(horizontal = 12.dp, vertical = 4.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(6.dp)
                        .background(color, RoundedCornerShape(3.dp))
                )
                Spacer(Modifier.width(8.dp))
                Text(status, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, color = color)
            }
        }
    }
}
