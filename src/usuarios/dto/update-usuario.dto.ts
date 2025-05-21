import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsEmail, Length, IsOptional } from 'class-validator';

export class UpdateUsuarioDto {
  @ApiPropertyOptional({ 
    description: 'Nombre del usuario',
    maxLength: 100,
    example: 'Juan Pérez'
  })
  @IsOptional()
  @IsString()
  @Length(1, 100)
  nombre?: string;

  @ApiPropertyOptional({ 
    description: 'Correo electrónico del usuario',
    maxLength: 100,
    example: 'juan@email.com'
  })
  @IsOptional()
  @IsEmail()
  @Length(1, 100)
  email?: string;

  @ApiPropertyOptional({ 
    description: 'Contraseña del usuario',
    maxLength: 255,
    example: 'contraseña123'
  })
  @IsOptional()
  @IsString()
  @Length(1, 255)
  password?: string;
} 