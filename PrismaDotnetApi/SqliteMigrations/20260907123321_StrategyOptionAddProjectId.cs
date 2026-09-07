using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace PrismaApi.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class StrategyOptionAddProjectId : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<Guid>(
                name: "ProjectId",
                table: "StrategyOptions",
                type: "TEXT",
                nullable: true);

            migrationBuilder.Sql(@"
                UPDATE StrategyOptions
                SET ProjectId = (
                    SELECT s.ProjectId FROM Strategies s
                    WHERE s.Id = StrategyOptions.StrategyId
                )");

            migrationBuilder.AlterColumn<Guid>(
                name: "ProjectId",
                table: "StrategyOptions",
                type: "TEXT",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "TEXT",
                oldNullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_StrategyOptions_ProjectId",
                table: "StrategyOptions",
                column: "ProjectId");

            migrationBuilder.AddForeignKey(
                name: "FK_StrategyOptions_Projects_ProjectId",
                table: "StrategyOptions",
                column: "ProjectId",
                principalTable: "Projects",
                principalColumn: "Id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_StrategyOptions_Projects_ProjectId",
                table: "StrategyOptions");

            migrationBuilder.DropIndex(
                name: "IX_StrategyOptions_ProjectId",
                table: "StrategyOptions");

            migrationBuilder.DropColumn(
                name: "ProjectId",
                table: "StrategyOptions");
        }
    }
}
